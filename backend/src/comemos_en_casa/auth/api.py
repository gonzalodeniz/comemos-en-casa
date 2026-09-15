"""HTTP routes and FastAPI dependencies for Google OIDC authentication."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from comemos_en_casa.database import get_connection

from .models import User
from .service import (
    AuthRepository,
    AuthenticationError,
    AuthenticationFailed,
    AuthService,
    GoogleOidcConfiguration,
    SESSION_LIFETIME,
)

API_PREFIX = "/api/v1/auth"
SESSION_COOKIE_NAME = "cec_session"


class MeResponse(BaseModel):
    """The deliberately small authenticated-user representation exposed to the browser."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    email: str
    display_name: str | None = Field(serialization_alias="displayName")
    picture_url: str | None = Field(serialization_alias="pictureUrl")


def _authentication_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
        content={"error": {"code": code, "message": message}},
    )


def _oidc_configuration(application: FastAPI) -> GoogleOidcConfiguration:
    configuration = application.state.settings.google_oidc
    if configuration is None:
        raise HTTPException(status_code=503, detail="Google authentication is not configured")
    return GoogleOidcConfiguration(
        client_id=configuration.client_id,
        client_secret=configuration.client_secret,
        redirect_uri=configuration.redirect_uri,
    )


def _attach_session_cookie(response: Response, token: str, *, secure: bool) -> None:
    """Set an HttpOnly browser cookie without putting its bearer token in JSON."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def current_user_dependency(
    request: Request,
    response: Response,
    connection: Any = Depends(get_connection),
) -> User:
    """Resolve and renew an opaque session for future protected mutation routes."""
    try:
        user = AuthService(AuthRepository(connection)).current_user(request.cookies.get(SESSION_COOKIE_NAME))
    except AuthenticationError as error:
        raise HTTPException(
            status_code=401,
            detail="Authentication is required",
            headers={"WWW-Authenticate": "Session", "Cache-Control": "no-store"},
        ) from error
    _attach_session_cookie(
            response,
            request.cookies[SESSION_COOKIE_NAME],
            secure=request.url.scheme == "https",
        )
    return user


CurrentUser = Annotated[User, Depends(current_user_dependency)]


def register_routes(application: FastAPI) -> None:
    """Register public auth endpoints; recipe visibility remains outside this module."""

    @application.get(f"{API_PREFIX}/login", status_code=307, include_in_schema=False)
    def login_start(connection: Any = Depends(get_connection)) -> RedirectResponse:
        configuration = _oidc_configuration(application)
        service = AuthService(AuthRepository(connection))
        attempt = service.begin_login()
        response = RedirectResponse(
            url=service.authorization_url(configuration, attempt),
            status_code=307,
            headers={"Cache-Control": "no-store"},
        )
        return response

    @application.get(f"{API_PREFIX}/callback", response_model=None, include_in_schema=False)
    def login_callback(
        request: Request,
        state: str | None = None,
        code: str | None = None,
        connection: Any = Depends(get_connection),
    ) -> RedirectResponse | JSONResponse:
        if not state or not code:
            return _authentication_response(400, "authentication_failed", "OAuth callback is incomplete")
        try:
            user, token, _ = AuthService(AuthRepository(connection)).complete_login(
                _oidc_configuration(application), state=state, code=code
            )
        except AuthenticationFailed:
            return _authentication_response(401, "authentication_failed", "Google authentication failed")
        response = RedirectResponse(
            url=application.state.settings.frontend_url,
            status_code=303,
            headers={"Cache-Control": "no-store"},
        )
        _attach_session_cookie(
            response,
            token,
            secure=request.url.scheme == "https",
        )
        return response

    @application.post(f"{API_PREFIX}/logout", status_code=204, include_in_schema=False)
    def logout(request: Request, connection: Any = Depends(get_connection)) -> Response:
        AuthService(AuthRepository(connection)).logout(request.cookies.get(SESSION_COOKIE_NAME))
        response = Response(status_code=204, headers={"Cache-Control": "no-store"})
        response.delete_cookie(
            SESSION_COOKIE_NAME,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            path="/",
        )
        return response

    @application.get(f"{API_PREFIX}/me", response_model=MeResponse)
    def me(response: Response, user: CurrentUser) -> MeResponse:
        response.headers["Cache-Control"] = "no-store"
        return MeResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            picture_url=user.picture_url,
        )
