"""API View endpoints for Authentication, Identity, and Role Administration."""
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts import services
from apps.accounts.models import Role, User
from apps.accounts.permissions import IsAdminOrSuperUser
from apps.accounts.serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RoleSerializer,
    TokenRefreshSerializer,
    UserAdminCreateSerializer,
    UserRoleAssignSerializer,
    UserSerializer,
    UserStatusUpdateSerializer,
)
from apps.accounts.throttles import AuthRateThrottle


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Inject secure, HttpOnly credentials into browser cookie headers."""
    secure = getattr(settings, "JWT_COOKIE_SECURE", False)
    samesite = getattr(settings, "JWT_COOKIE_SAMESITE", "Lax")

    response.set_cookie(
        key=getattr(settings, "JWT_AUTH_COOKIE", "gqt_access_token"),
        value=access_token,
        max_age=15 * 60,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=getattr(settings, "JWT_COOKIE_PATH", "/"),
    )
    response.set_cookie(
        key=getattr(settings, "JWT_REFRESH_COOKIE", "gqt_refresh_token"),
        value=refresh_token,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=getattr(settings, "JWT_REFRESH_COOKIE_PATH", "/api/v1/auth/"),
    )


def _clear_auth_cookies(response: Response) -> None:
    """Purge authentication cookies upon logout."""
    response.delete_cookie(
        key=getattr(settings, "JWT_AUTH_COOKIE", "gqt_access_token"),
        path=getattr(settings, "JWT_COOKIE_PATH", "/"),
    )
    response.delete_cookie(
        key=getattr(settings, "JWT_REFRESH_COOKIE", "gqt_refresh_token"),
        path=getattr(settings, "JWT_REFRESH_COOKIE_PATH", "/api/v1/auth/"),
    )


class LoginView(APIView):
    """Authenticate credentials, set secure HttpOnly cookies, and return active user profile."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=LoginSerializer, responses={200: UserSerializer})
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, refresh = services.authenticate_and_issue_tokens(
            request=request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        user_data = UserSerializer(user).data
        response = Response(
            {
                "user": user_data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_200_OK,
        )

        _set_auth_cookies(response, str(refresh.access_token), str(refresh))
        return response


class LogoutView(APIView):
    """Invalidate refresh token and clear authentication cookies."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=TokenRefreshSerializer, responses={200: dict})
    def post(self, request: Request) -> Response:
        refresh_str = request.data.get("refresh")
        services.logout_user(request=request, raw_refresh_token=refresh_str)

        response = Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        _clear_auth_cookies(response)
        return response


class CurrentUserView(APIView):
    """Retrieve authenticated user profile, roles, and identity details."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request: Request) -> Response:
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    """Rotate refresh token and issue a fresh access token."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=TokenRefreshSerializer, responses={200: dict})
    def post(self, request: Request) -> Response:
        refresh_str = request.data.get("refresh")
        new_refresh, new_access = services.rotate_refresh_token(
            request=request, raw_refresh_token=refresh_str
        )

        response = Response(
            {
                "access": new_access,
                "refresh": str(new_refresh),
            },
            status=status.HTTP_200_OK,
        )
        _set_auth_cookies(response, new_access, str(new_refresh))
        return response


class PasswordChangeView(APIView):
    """Change current user password after verifying current credentials."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PasswordChangeSerializer, responses={200: dict})
    def post(self, request: Request) -> Response:
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        services.change_user_password(
            request=request,
            user=request.user,
            new_password=serializer.validated_data["new_password"],
        )

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """Initiate password reset workflow without exposing account existence."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: dict})
    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.initiate_password_reset(
            request=request,
            email=serializer.validated_data["email"],
        )

        return Response(
            {
                "message": (
                    "If an account with that email exists, password reset instructions "
                    "have been dispatched."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Complete password reset using a verified, single-use token."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: dict})
    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        services.confirm_password_reset(
            request=request,
            user=user,
            new_password=serializer.validated_data["new_password"],
        )

        return Response(
            {"message": "Password has been reset successfully. You may now log in."},
            status=status.HTTP_200_OK,
        )


class RoleListView(generics.ListAPIView):
    """List all available operational roles for role assignment."""

    permission_classes = [permissions.IsAuthenticated]
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    pagination_class = None


@extend_schema_view(
    list=extend_schema(description="List user accounts across the enterprise."),
    retrieve=extend_schema(description="Retrieve user profile by UUID."),
    create=extend_schema(description="Provision a new user account with role assignments."),
)
class UserAdminViewSet(viewsets.ModelViewSet):
    """Administrative management of platform user accounts and role assignments."""

    permission_classes = [IsAdminOrSuperUser]
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return UserAdminCreateSerializer
        return UserSerializer

    def perform_create(self, serializer: UserAdminCreateSerializer) -> None:
        roles = serializer.validated_data.pop("roles", [])
        password = serializer.validated_data.pop("password")
        user = User.objects.create_user(password=password, **serializer.validated_data)
        if roles:
            services.assign_roles_to_user(
                target_user=user,
                role_codes=roles,
                assigned_by=self.request.user,
                request=self.request,
            )

    @action(detail=True, methods=["patch"])
    def status(self, request: Request, pk=None) -> Response:
        """Activate or deactivate a user account."""
        user = self.get_object()
        serializer = UserStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_user = services.update_user_status(
            target_user=user,
            is_active=serializer.validated_data["is_active"],
            updated_by=request.user,
            request=request,
        )
        return Response(UserSerializer(updated_user).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def roles(self, request: Request, pk=None) -> Response:
        """Assign or revoke operational roles for a user account."""
        user = self.get_object()
        serializer = UserRoleAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        active_roles = services.assign_roles_to_user(
            target_user=user,
            role_codes=serializer.validated_data["role_codes"],
            assigned_by=request.user,
            request=request,
        )
        return Response({"roles": active_roles}, status=status.HTTP_200_OK)
