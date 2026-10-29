"""Serializers for Identity, Authentication, and Role Management."""
from typing import List
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from apps.accounts.models import Role, RoleCatalog, User
from apps.core.models import AuditLog


class RoleSerializer(serializers.ModelSerializer):
    """Serializer representing an operational role in the catalog."""

    class Meta:
        model = Role
        fields = ["id", "code", "name", "description", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    """Read-only user profile serializer representing an authenticated user."""

    roles = serializers.SerializerMethodField()
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "is_active",
            "is_staff",
            "is_superuser",
            "roles",
            "created_at",
            "last_login",
        ]
        read_only_fields = fields

    def get_roles(self, obj: User) -> List[str]:
        return obj.get_active_roles()


class LoginSerializer(serializers.Serializer):
    """Serializer for authenticating with normalized email and password."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate_email(self, value: str) -> str:
        return value.lower().strip()


class TokenRefreshSerializer(serializers.Serializer):
    """Optional payload when refreshing authentication credentials."""

    refresh = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional bearer refresh token; if omitted, cookie is utilized.",
    )


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing an authenticated user's password."""

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "New passwords do not match."})

        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "The current password provided is incorrect."})

        # Run Django password validators
        password_validation.validate_password(attrs["new_password"], user=user)
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset email."""

    email = serializers.EmailField(required=True)

    def validate_email(self, value: str) -> str:
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for completing password reset via verified token."""

    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})

        try:
            uid = urlsafe_base64_decode(attrs["uidb64"]).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"token": "Password reset token is invalid or has expired."})

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Password reset token is invalid or has expired."})

        password_validation.validate_password(attrs["new_password"], user=user)
        attrs["user"] = user
        return attrs


class UserAdminCreateSerializer(serializers.ModelSerializer):
    """Serializer used by Platform Administrators to create user accounts with role assignments."""

    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )
    roles = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "is_active",
            "roles",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_email(self, value: str) -> str:
        normalized = value.lower().strip()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("A user account with this email address already exists.")
        return normalized

    def validate_password(self, value: str) -> str:
        password_validation.validate_password(value)
        return value

    def validate_roles(self, values: List[str]) -> List[str]:
        valid_codes = set(Role.objects.filter(is_active=True).values_list("code", flat=True))
        invalid = [code for code in values if code not in valid_codes]
        if invalid:
            raise serializers.ValidationError(f"Invalid or inactive role codes: {', '.join(invalid)}")
        return values


class UserStatusUpdateSerializer(serializers.Serializer):
    """Serializer for activating or deactivating user accounts."""

    is_active = serializers.BooleanField(required=True)


class UserRoleAssignSerializer(serializers.Serializer):
    """Serializer for assigning roles to a user account."""

    role_codes = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=True,
    )

    def validate_role_codes(self, values: List[str]) -> List[str]:
        valid_codes = set(Role.objects.filter(is_active=True).values_list("code", flat=True))
        invalid = [code for code in values if code not in valid_codes]
        if invalid:
            raise serializers.ValidationError(f"Invalid role codes: {', '.join(invalid)}")
        return values


class UserAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer used by Platform Administrators to update permitted user details."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
        ]

    def validate_phone_number(self, value: str) -> str:
        return value.strip()


def _is_sensitive_key(key: str) -> bool:
    sensitive_patterns = (
        "password",
        "token",
        "secret",
        "refresh",
        "access",
        "api_key",
        "credentials",
        "otp",
        "hash",
    )
    key_lower = str(key).lower()
    return any(pat in key_lower for pat in sensitive_patterns)


def _sanitize_audit_payload(item, key_name: str = ""):
    if key_name and _is_sensitive_key(key_name):
        return "[REDACTED]"
    if isinstance(item, dict):
        return {
            k: ("[REDACTED]" if _is_sensitive_key(k) else _sanitize_audit_payload(v, k))
            for k, v in item.items()
        }
    if isinstance(item, (list, tuple, set)):
        return [_sanitize_audit_payload(elem, key_name) for elem in item]
    return item


class UserAuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for auditing historical administrative actions on user accounts."""

    actor_email = serializers.SerializerMethodField()
    actor_name = serializers.SerializerMethodField()
    changes = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "action",
            "resource_type",
            "resource_id",
            "actor_email",
            "actor_name",
            "ip_address",
            "user_agent",
            "correlation_id",
            "changes",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_email(self, obj: AuditLog) -> str:
        return obj.user.email if obj.user else "System"

    def get_actor_name(self, obj: AuditLog) -> str:
        return obj.user.full_name if obj.user else "System"

    def get_changes(self, obj: AuditLog) -> dict:
        data = obj.changes or {}
        return _sanitize_audit_payload(data)

