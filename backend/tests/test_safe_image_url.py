import socket
import io

import pytest
import threading
import time

import app.safe_image_url as safe_image_url
from app.safe_image_url import UnsafeImageURL, _PinnedHTTPConnection, safe_fetch_image


def dns_records(host, port, *, type):
    ip = "93.184.216.34" if host == "public.example" else "127.0.0.1"
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]


class FakeResponse:
    def __init__(self, status, body=b"image", headers=None):
        self.status, self.body, self.headers, self.offset = status, body, headers or {}, 0
    def getheader(self, key): return self.headers.get(key)
    def close(self): pass
    def read(self, amount=-1):
        if amount == 0: return b""
        result = self.body[self.offset:self.offset + amount]
        self.offset += len(result)
        return result
    def read1(self, amount=-1): return self.read(amount)
    def isclosed(self): return False


class FakeConnection:
    def __init__(self, response): self.response = response; self.sock = self; self.timeout = None
    def request(self, method, path, headers): self.request_data = (method, path, headers)
    def getresponse(self): return self.response
    def settimeout(self, timeout): self.timeout = timeout
    def close(self): pass


def test_url_fetch_pins_each_hop_and_revalidates_redirect_dns():
    calls = []
    responses = [FakeResponse(302, headers={"Location":"https://public.example/final"}), FakeResponse(200, b"ok")]
    def factory(scheme, host, port, pinned, timeout):
        calls.append((scheme, host, port, pinned, timeout))
        return FakeConnection(responses.pop(0))
    data, final = safe_fetch_image("https://public.example/start", resolver=dns_records, connection_factory=factory)
    assert data == b"ok"
    assert final == "https://public.example/final"
    assert [call[3] for call in calls] == ["93.184.216.34", "93.184.216.34"]
    assert all(call[4] <= 10 for call in calls)


def test_url_fetch_rejects_private_dns_answer_before_connecting():
    called = False
    def factory(*args):
        nonlocal called
        called = True
        raise AssertionError("must not connect")
    with pytest.raises(UnsafeImageURL, match="non-public"):
        safe_fetch_image("http://private.example/a", resolver=dns_records, connection_factory=factory)
    assert not called


def test_redirect_to_private_destination_is_rejected_before_second_connection():
    calls = []
    responses = [FakeResponse(302, headers={"Location":"http://private.example/metadata"})]
    def factory(*args):
        calls.append(args)
        return FakeConnection(responses.pop(0))
    with pytest.raises(UnsafeImageURL, match="non-public"):
        safe_fetch_image("http://public.example/start", resolver=dns_records, connection_factory=factory)
    assert len(calls) == 1


def test_http_connection_uses_and_verifies_pinned_peer(monkeypatch):
    class Sock:
        def getpeername(self): return ("93.184.216.34", 80)
        def close(self): pass
    monkeypatch.setattr(socket, "create_connection", lambda address, timeout: Sock())
    connection = _PinnedHTTPConnection("public.example", 80, "93.184.216.34", 1)
    connection.connect()
    assert connection.sock.getpeername()[0] == "93.184.216.34"


def test_http_connection_rejects_mismatched_actual_peer(monkeypatch):
    class Sock:
        def getpeername(self): return ("127.0.0.1", 80)
        def close(self): pass
    monkeypatch.setattr(socket, "create_connection", lambda address, timeout: Sock())
    connection = _PinnedHTTPConnection("public.example", 80, "93.184.216.34", 1)
    with pytest.raises(UnsafeImageURL, match="peer"):
        connection.connect()


def test_slow_dns_timeouts_do_not_exceed_bounded_resolver_capacity(monkeypatch):
    monkeypatch.setattr(safe_image_url, "TOTAL_TIMEOUT_SECONDS", 0.02)
    release_dns = threading.Event()
    counter_lock = threading.Lock()
    started = 0
    def slow_resolver(host, port, *, type):
        nonlocal started
        with counter_lock:
            started += 1
        release_dns.wait(2)
        return dns_records(host, port, type=type)
    outcomes = []
    for index in range(8):
        try:
            safe_fetch_image(f"http://public.example/{index}", resolver=slow_resolver,
                connection_factory=lambda *_: pytest.fail("must not connect"))
        except UnsafeImageURL as error:
            outcomes.append(str(error))
    assert started <= safe_image_url._DNS_WORKERS
    assert any("capacity" in outcome for outcome in outcomes)
    release_dns.set()

    deadline = time.monotonic() + 1
    acquired = False
    while time.monotonic() < deadline:
        acquired = safe_image_url._dns_admission.acquire(blocking=False)
        if acquired:
            break
        time.sleep(0.01)
    assert acquired
    if acquired:
        safe_image_url._dns_admission.release()

    data, _ = safe_fetch_image("http://public.example/ready", resolver=dns_records,
        connection_factory=lambda *_: FakeConnection(FakeResponse(200, b"ok")))
    assert data == b"ok"


def test_connection_close_response_keeps_body_socket_until_read(monkeypatch):
    class ResponseSocket:
        def __init__(self):
            self.closed = False
            self.stream = io.BytesIO(b"HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Length: 5\r\n\r\nimage")
            self.timeouts = []
        def sendall(self, data): pass
        def makefile(self, mode): return self.stream
        def settimeout(self, timeout): self.timeouts.append(timeout)
        def close(self): self.closed = True

    sock = ResponseSocket()
    monkeypatch.setattr(_PinnedHTTPConnection, "connect", lambda connection: setattr(connection, "sock", sock))
    data, final = safe_fetch_image("http://public.example/image", resolver=dns_records)
    assert data == b"image"
    assert final == "http://public.example/image"
    assert sock.closed and sock.stream.closed
    assert len(sock.timeouts) >= 2


def test_response_timeout_uses_remaining_total_deadline_after_socket_detached():
    moments = iter([0, 0, 0, 3, 7, 10])
    connection = FakeConnection(FakeResponse(200, b"image"))
    original_getresponse = connection.getresponse
    timeouts = []
    connection.settimeout = timeouts.append
    def getresponse():
        response = original_getresponse()
        connection.sock = None
        return response
    connection.getresponse = getresponse
    with pytest.raises(UnsafeImageURL, match="timed out"):
        safe_fetch_image("http://public.example/image", resolver=dns_records,
                         connection_factory=lambda *_: connection, clock=lambda: next(moments))
    assert timeouts == [7, 3]


def test_fixed_length_close_response_releases_real_socket_after_body(monkeypatch):
    client, server = socket.socketpair()
    try:
        server.sendall(b"HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Length: 5\r\n\r\nimage")
        monkeypatch.setattr(_PinnedHTTPConnection, "connect", lambda connection: setattr(connection, "sock", client))
        data, _ = safe_fetch_image("http://public.example/image", resolver=dns_records)
        assert data == b"image"
        assert client.fileno() == -1
    finally:
        client.close()
        server.close()
