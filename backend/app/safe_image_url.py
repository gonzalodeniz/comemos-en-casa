"""Fetch remote image bytes while pinning each HTTP(S) connection to validated DNS."""
from __future__ import annotations

import concurrent.futures
import http.client
import ipaddress
import socket
import threading
import time
from urllib.parse import urljoin, urlsplit

MAX_REDIRECTS = 5
MAX_BYTES = 2 * 1024 * 1024
TOTAL_TIMEOUT_SECONDS = 10.0
REDIRECT_CODES = {301, 302, 303, 307, 308}
_DNS_WORKERS = 4
_dns_pool = concurrent.futures.ThreadPoolExecutor(max_workers=_DNS_WORKERS, thread_name_prefix="image-dns")
_dns_admission = threading.BoundedSemaphore(_DNS_WORKERS)


class UnsafeImageURL(ValueError):
    pass


def _resolve_public(host: str, port: int, resolver=socket.getaddrinfo) -> list[str]:
    try:
        literal = ipaddress.ip_address(host)
        addresses = [literal]
    except ValueError:
        try:
            records = resolver(host, port, type=socket.SOCK_STREAM)
        except OSError as error:
            raise UnsafeImageURL("Could not resolve image host") from error
        addresses = []
        for record in records:
            try:
                addresses.append(ipaddress.ip_address(record[4][0]))
            except ValueError as error:
                raise UnsafeImageURL("Invalid DNS address") from error
    unique = list(dict.fromkeys(addresses))
    if not unique or any(not address.is_global for address in unique):
        raise UnsafeImageURL("Image URL resolves to a non-public address")
    return [str(address) for address in unique]


def _resolve_before_deadline(host: str, port: int, resolver, remaining: float) -> list[str]:
    if not _dns_admission.acquire(blocking=False):
        raise UnsafeImageURL("Image DNS capacity temporarily unavailable")
    try:
        future = _dns_pool.submit(_resolve_public, host, port, resolver)
    except RuntimeError as error:
        _dns_admission.release()
        raise UnsafeImageURL("Image DNS capacity unavailable") from error
    future.add_done_callback(lambda _future: _dns_admission.release())
    try:
        return future.result(timeout=max(0.001, remaining))
    except concurrent.futures.TimeoutError as error:
        future.cancel()
        raise UnsafeImageURL("Image URL request timed out") from error


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, pinned_ip: str, timeout: float):
        super().__init__(host, port, timeout=timeout)
        self.pinned_ip = pinned_ip

    def connect(self) -> None:
        sock = socket.create_connection((self.pinned_ip, self.port), self.timeout)
        try:
            peer = ipaddress.ip_address(sock.getpeername()[0])
            if peer != ipaddress.ip_address(self.pinned_ip):
                raise UnsafeImageURL("Connected peer did not match validated address")
            if self._tunnel_host:
                self._tunnel()
            # `self.host` remains the URL hostname, preserving SNI and certificate validation.
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except Exception:
            sock.close()
            raise


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, pinned_ip: str, timeout: float):
        super().__init__(host, port, timeout=timeout)
        self.pinned_ip = pinned_ip

    def connect(self) -> None:
        sock = socket.create_connection((self.pinned_ip, self.port), self.timeout)
        peer = ipaddress.ip_address(sock.getpeername()[0])
        if peer != ipaddress.ip_address(self.pinned_ip):
            sock.close()
            raise UnsafeImageURL("Connected peer did not match validated address")
        self.sock = sock


def safe_fetch_image(url: str, *, resolver=socket.getaddrinfo, connection_factory=None,
                     clock=time.monotonic, max_bytes: int = MAX_BYTES) -> tuple[bytes, str]:
    """Fetch at most 2 MiB; every redirect receives a fresh DNS validation and pinned socket."""
    deadline = clock() + TOTAL_TIMEOUT_SECONDS
    current = url
    for redirect_count in range(MAX_REDIRECTS + 1):
        parsed = urlsplit(current)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise UnsafeImageURL("Only credential-free HTTP(S) URLs are supported")
        try:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except ValueError as error:
            raise UnsafeImageURL("Invalid URL port") from error
        if port != (443 if parsed.scheme == "https" else 80):
            raise UnsafeImageURL("Invalid URL port")
        host = parsed.hostname
        remaining = deadline - clock()
        if remaining <= 0:
            raise UnsafeImageURL("Image URL request timed out")
        answers = _resolve_before_deadline(host, port, resolver, remaining)
        remaining = deadline - clock()
        if remaining <= 0:
            raise UnsafeImageURL("Image URL request timed out")
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        if connection_factory:
            connection = connection_factory(parsed.scheme, host, port, answers[0], remaining)
        elif parsed.scheme == "https":
            connection = _PinnedHTTPSConnection(host, port, answers[0], remaining)
        else:
            connection = _PinnedHTTPConnection(host, port, answers[0], remaining)
        host_header = f"[{host}]" if ":" in host else host
        if parsed.port is not None:
            host_header = f"{host_header}:{port}"
        response = None
        try:
            connection.request("GET", path, headers={"Host": host_header, "Accept": "image/jpeg,image/png,image/webp", "Connection": "close"})
            # HTTPConnection detaches its socket for a closing response, but the
            # response file keeps the underlying descriptor alive until closed.
            response_socket = connection.sock
            remaining = deadline - clock()
            if remaining <= 0:
                raise UnsafeImageURL("Image URL request timed out")
            response_socket.settimeout(remaining)
            response = connection.getresponse()
            if response.status in REDIRECT_CODES:
                location = response.getheader("Location")
                response.read(0)
                connection.close()
                if not location or redirect_count >= MAX_REDIRECTS:
                    raise UnsafeImageURL("Too many or invalid image redirects")
                current = urljoin(current, location)
                continue
            if response.status != 200:
                raise UnsafeImageURL("Image server returned an unsuccessful status")
            content_length = response.getheader("Content-Length")
            if content_length:
                try:
                    declared_size = int(content_length)
                except ValueError as error:
                    raise UnsafeImageURL("Invalid image Content-Length") from error
                if declared_size < 0 or declared_size > max_bytes:
                    raise UnsafeImageURL("Image exceeds 2 MiB")
            chunks = bytearray()
            while True:
                remaining = deadline - clock()
                if remaining <= 0:
                    raise UnsafeImageURL("Image URL request timed out")
                response_socket.settimeout(remaining)
                chunk = response.read1(min(65536, max_bytes + 1 - len(chunks)))
                if not chunk:
                    break
                chunks.extend(chunk)
                if len(chunks) > max_bytes:
                    raise UnsafeImageURL("Image exceeds 2 MiB")
                # A complete fixed-length response closes its file and may release
                # the detached socket immediately, so do not set its timeout again.
                if response.isclosed():
                    break
            return bytes(chunks), current
        except (OSError, http.client.HTTPException) as error:
            raise UnsafeImageURL("Could not retrieve image URL") from error
        finally:
            if response is not None:
                response.close()
            connection.close()
    raise UnsafeImageURL("Too many image redirects")
