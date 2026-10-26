"""Authentication backends: HttpOnly Cookie JWT Authentication with Bearer fallback."""
from typing import Optional, Tuple
from django.conf import settings
from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import (
    AuthUser,
    JWTAuthentication,
)
from rest_framework_simplejwt.tokens import Token


class HttpOnlyCookieJWTAuthentication(JWTAuthentication):
    """Authenticates against a secure HttpOnly cookie (gqt_access_token) with fallback to Bearer header."""

    def authenticate(self, request: Request) -> Optional[Tuple[AuthUser, Token]]:
        cookie_name = getattr(settings, "JWT_AUTH_COOKIE", "gqt_access_token")
        raw_token = request.COOKIES.get(cookie_name)

        if raw_token is not None:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            if not user.is_active:
                raise exceptions.AuthenticationFailed("Account is deactivated.")
            return user, validated_token

        # Fallback to standard Authorization: Bearer <token>
        header_auth = super().authenticate(request)
        if header_auth is not None:
            user, validated_token = header_auth
            if not user.is_active:
                raise exceptions.AuthenticationFailed("Account is deactivated.")
            return user, validated_token

        return None
