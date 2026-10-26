"""Domain service layer for Identity, Authentication, and Role Assignments."""
import logging
from typing import List, Optional, Tuple
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from apps.accounts.models import Role, RoleCatalog, User, UserRoleAssignment
from apps.core.models import AuditLog

logger = logging.getLogger("apps.accounts")


def _get_client_ip(request) -> Optional[str]:
    """Safely extract remote IP address from request."""
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_correlation_id(request) -> str:
    """Retrieve correlation ID attached by CorrelationIdMiddleware."""
    return getattr(request, "correlation_id", "") if request else ""


def log_security_event(
    action: str,
    resource_id: str,
    user: Optional[User] = None,
    request=None,
    changes: Optional[dict] = None,
) -> None:
    """Record an immutable security event into core_audit_log with zero secret disclosure."""
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            resource_type="accounts.User",
            resource_id=str(resource_id),
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500] if request else "",
            correlation_id=_get_correlation_id(request),
            changes=changes or {},
        )
    except Exception as exc:
        logger.warning("Failed to record security audit log: %s", exc)


def authenticate_and_issue_tokens(
    request, email: str, password: str
) -> Tuple[User, RefreshToken]:
    """Verify user credentials, validate account status, and issue a refreshed token pair."""
    normalized_email = email.lower().strip()
    try:
        user = User.objects.get(email=normalized_email)
    except User.DoesNotExist:
        log_security_event(
            action="LOGIN_FAILED",
            resource_id=normalized_email,
            request=request,
            changes={"reason": "User not found"},
        )
        raise exceptions.AuthenticationFailed("Invalid email or password.")

    if not user.check_password(password):
        log_security_event(
            action="LOGIN_FAILED",
            resource_id=str(user.id),
            user=user,
            request=request,
            changes={"reason": "Bad password"},
        )
        raise exceptions.AuthenticationFailed("Invalid email or password.")

    if not user.is_active:
        log_security_event(
            action="LOGIN_FAILED_DEACTIVATED",
            resource_id=str(user.id),
            user=user,
            request=request,
            changes={"reason": "Account inactive"},
        )
        raise exceptions.AuthenticationFailed("Account is deactivated. Please contact your administrator.")

    # Update last login timestamp
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    # Issue JWT tokens
    refresh = RefreshToken.for_user(user)

    log_security_event(
        action="LOGIN_SUCCESS",
        resource_id=str(user.id),
        user=user,
        request=request,
        changes={"email": user.email},
    )

    return user, refresh


def rotate_refresh_token(request, raw_refresh_token: Optional[str] = None) -> Tuple[RefreshToken, str]:
    """Rotate a valid refresh token with replay-detection and blacklist enforcement."""
    token_str = raw_refresh_token
    if not token_str:
        cookie_name = getattr(settings, "JWT_REFRESH_COOKIE", "gqt_refresh_token")
        token_str = request.COOKIES.get(cookie_name)

    if not token_str:
        raise exceptions.AuthenticationFailed("No refresh token provided.")

    try:
        old_token = RefreshToken(token_str)
        user_id = old_token.payload.get("user_id")
        user = User.objects.get(id=user_id)
        if not user.is_active:
            raise exceptions.AuthenticationFailed("Account is deactivated.")

        # Blacklist old refresh token and generate new family
        old_token.blacklist()
        new_refresh = RefreshToken.for_user(user)
        new_access = str(new_refresh.access_token)

        return new_refresh, new_access
    except (TokenError, User.DoesNotExist) as exc:
        raise exceptions.AuthenticationFailed("Refresh token is invalid, expired, or has already been used.")


def logout_user(request, raw_refresh_token: Optional[str] = None) -> None:
    """Invalidate active refresh tokens and log user sign-out."""
    token_str = raw_refresh_token
    if not token_str:
        cookie_name = getattr(settings, "JWT_REFRESH_COOKIE", "gqt_refresh_token")
        token_str = request.COOKIES.get(cookie_name)

    if token_str:
        try:
            token = RefreshToken(token_str)
            token.blacklist()
        except TokenError:
            pass  # Token may already be expired or blacklisted

    if request.user and request.user.is_authenticated:
        log_security_event(
            action="LOGOUT",
            resource_id=str(request.user.id),
            user=request.user,
            request=request,
        )


def change_user_password(request, user: User, new_password: str) -> None:
    """Update user password securely and record the security event."""
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])

    log_security_event(
        action="PASSWORD_CHANGED",
        resource_id=str(user.id),
        user=user,
        request=request,
    )


def initiate_password_reset(request, email: str) -> bool:
    """Generate a single-use token and dispatch a reset notification without revealing account existence."""
    normalized_email = email.lower().strip()
    try:
        user = User.objects.get(email=normalized_email, is_active=True)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # In local/test environments, send to console or logger
        reset_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')}/auth/reset-password?uid={uid}&token={token}"
        logger.info("Password reset requested for [%s]. Reset Link: %s", normalized_email, reset_url)

        try:
            send_mail(
                subject="GQT HRMS — Password Reset Request",
                message=f"Hello {user.full_name},\n\nA password reset was requested for your GQT HRMS account.\nUse the following link to choose a new password:\n{reset_url}\n\nIf you did not make this request, please ignore this email.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@gqt.local"),
                recipient_list=[normalized_email],
                fail_silently=True,
            )
        except Exception as mail_err:
            logger.warning("Email delivery skipped (external SMTP not configured): %s", mail_err)

        log_security_event(
            action="PASSWORD_RESET_REQUESTED",
            resource_id=str(user.id),
            user=user,
            request=request,
            changes={"email": normalized_email},
        )
    except User.DoesNotExist:
        # Generic response; do not enumerate account existence
        pass

    return True


def confirm_password_reset(request, user: User, new_password: str) -> None:
    """Complete password reset with a verified single-use token."""
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])

    log_security_event(
        action="PASSWORD_RESET_COMPLETED",
        resource_id=str(user.id),
        user=user,
        request=request,
    )


@transaction.atomic
def assign_roles_to_user(
    target_user: User,
    role_codes: List[str],
    assigned_by: Optional[User] = None,
    request=None,
) -> List[str]:
    """Atomically synchronize active role assignments for a user account."""
    roles = Role.objects.filter(code__in=role_codes, is_active=True)
    role_map = {r.code: r for r in roles}

    # Deactivate existing roles not in the new set
    UserRoleAssignment.objects.filter(user=target_user, is_active=True).exclude(
        role__code__in=role_codes
    ).update(is_active=False)

    # Activate or create assignments
    for code in role_codes:
        if code in role_map:
            role = role_map[code]
            assignment, created = UserRoleAssignment.objects.get_or_create(
                user=target_user,
                role=role,
                defaults={"assigned_by": assigned_by, "is_active": True},
            )
            if not assignment.is_active:
                assignment.is_active = True
                assignment.assigned_by = assigned_by
                assignment.save(update_fields=["is_active", "assigned_by"])

    active_roles = target_user.get_active_roles()

    log_security_event(
        action="ROLES_UPDATED",
        resource_id=str(target_user.id),
        user=assigned_by,
        request=request,
        changes={"target_user": target_user.email, "roles": active_roles},
    )

    return active_roles


def update_user_status(
    target_user: User,
    is_active: bool,
    updated_by: User,
    request=None,
) -> User:
    """Update user account active state with safeguard preventing admin self-deactivation."""
    if target_user.id == updated_by.id and not is_active:
        raise exceptions.ValidationError("Administrators cannot deactivate their own account.")

    target_user.is_active = is_active
    target_user.save(update_fields=["is_active", "updated_at"])

    log_security_event(
        action="ACCOUNT_STATUS_CHANGED",
        resource_id=str(target_user.id),
        user=updated_by,
        request=request,
        changes={"is_active": is_active, "target_user": target_user.email},
    )

    return target_user
