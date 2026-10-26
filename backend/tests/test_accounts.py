"""Comprehensive verification suite for Identity, Authentication, and Role-Based Access Control (Phase 1)."""
import uuid
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.management import call_command
from django.db import IntegrityError
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import Role, RoleCatalog, UserRoleAssignment
from apps.accounts.services import assign_roles_to_user
from apps.core.models import AuditLog

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seed_roles(db):
    call_command("seed_roles")


@pytest.fixture
def test_password():
    return "P@ssw0rd12345!"


@pytest.fixture
def standard_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="student@gqt.local",
        password=test_password,
        first_name="Jane",
        last_name="Doe",
    )
    assign_roles_to_user(user, [RoleCatalog.STUDENT])
    return user


@pytest.fixture
def admin_user(db, seed_roles, test_password):
    user = User.objects.create_superuser(
        email="admin@gqt.local",
        password=test_password,
        first_name="System",
        last_name="Admin",
    )
    assign_roles_to_user(user, [RoleCatalog.ADMIN])
    return user


@pytest.fixture
def placement_head_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="head@gqt.local",
        password=test_password,
        first_name="Head",
        last_name="Director",
    )
    assign_roles_to_user(user, [RoleCatalog.PLACEMENT_HEAD])
    return user


# ==============================================================================
# Step 2: Custom User Model Tests (1-4)
# ==============================================================================

@pytest.mark.django_db
def test_01_custom_user_creation_with_uuid():
    """Verify custom user creation assigns a valid UUID primary key."""
    user = User.objects.create_user(email="test.user@gqt.local", password="StrongPassword1!")
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "test.user@gqt.local"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_02_email_normalization():
    """Verify email normalization lowercases and strips whitespace."""
    user = User.objects.create_user(email="  UPPERCASE.Student@GQT.LOCAL  ", password="StrongPassword1!")
    assert user.email == "uppercase.student@gqt.local"


@pytest.mark.django_db
def test_03_email_uniqueness_enforced():
    """Verify case-insensitive database uniqueness prevents duplicate accounts."""
    User.objects.create_user(email="unique.student@gqt.local", password="StrongPassword1!")
    with pytest.raises(Exception):
        User.objects.create_user(email="UNIQUE.student@gqt.local", password="AnotherPassword1!")


@pytest.mark.django_db
def test_04_password_hashing_security(test_password):
    """Verify password is cryptographically hashed and Argon2id is primary configured hasher."""
    from config.settings import base

    assert base.PASSWORD_HASHERS[0] == "django.contrib.auth.hashers.Argon2PasswordHasher"

    user = User.objects.create_user(email="hashed@gqt.local", password=test_password)
    assert user.password != test_password
    assert not user.password.startswith(test_password)
    assert user.check_password(test_password) is True
    assert user.check_password("WrongPassword123") is False


# ==============================================================================
# Step 4: Secure Authentication APIs Tests (5-10)
# ==============================================================================

@pytest.mark.django_db
def test_05_successful_login_sets_httponly_cookies_and_returns_profile(api_client, standard_user, test_password):
    """Verify login issues HttpOnly cookies and returns the serialized user profile."""
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": "student@gqt.local", "password": test_password},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["email"] == "student@gqt.local"
    assert RoleCatalog.STUDENT in response.data["user"]["roles"]

    # Verify HttpOnly Cookie injection
    access_cookie = response.cookies.get(settings.JWT_AUTH_COOKIE)
    refresh_cookie = response.cookies.get(settings.JWT_REFRESH_COOKIE)
    assert access_cookie is not None
    assert access_cookie["httponly"] is True
    assert refresh_cookie is not None
    assert refresh_cookie["httponly"] is True


@pytest.mark.django_db
def test_06_invalid_login_returns_generic_error(api_client, standard_user):
    """Verify failed login returns a generic error to prevent email enumeration."""
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": "student@gqt.local", "password": "WrongPassword123!"},
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid email or password" in str(response.data)


@pytest.mark.django_db
def test_07_inactive_account_login_denied(api_client, standard_user, test_password):
    """Verify deactivated user accounts cannot authenticate."""
    standard_user.is_active = False
    standard_user.save()

    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": standard_user.email, "password": test_password},
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "deactivated" in str(response.data).lower()


@pytest.mark.django_db
def test_08_logout_blacklists_refresh_token_and_clears_cookies(api_client, standard_user, test_password):
    """Verify logout purges auth cookies and blacklists the refresh token."""
    login_resp = api_client.post(
        "/api/v1/auth/login/",
        {"email": standard_user.email, "password": test_password},
        format="json",
    )
    refresh_token = login_resp.data["tokens"]["refresh"]

    logout_resp = api_client.post(
        "/api/v1/auth/logout/",
        {"refresh": refresh_token},
        format="json",
    )
    assert logout_resp.status_code == status.HTTP_200_OK

    # Attempting to refresh with the blacklisted token must fail
    refresh_resp = api_client.post(
        "/api/v1/auth/refresh/",
        {"refresh": refresh_token},
        format="json",
    )
    assert refresh_resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_09_authenticated_current_user_endpoint(api_client, standard_user):
    """Verify GET /api/v1/auth/me/ returns current identity."""
    api_client.force_authenticate(user=standard_user)
    response = api_client.get("/api/v1/auth/me/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == standard_user.email
    assert response.data["first_name"] == standard_user.first_name


@pytest.mark.django_db
def test_10_unauthenticated_access_denied(api_client):
    """Verify deny-by-default behavior rejects unauthenticated requests."""
    response = api_client.get("/api/v1/auth/me/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==============================================================================
# Step 3: RBAC & Object-Level Authorization Tests (11-14)
# ==============================================================================

@pytest.mark.django_db
def test_11_role_based_authorization_grants_access_to_authorized_roles(api_client, admin_user, standard_user):
    """Verify admin endpoint allows Admin role and forbids Student role."""
    api_client.force_authenticate(user=standard_user)
    student_resp = api_client.get("/api/v1/auth/users/")
    assert student_resp.status_code == status.HTTP_403_FORBIDDEN

    api_client.force_authenticate(user=admin_user)
    admin_resp = api_client.get("/api/v1/auth/users/")
    assert admin_resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_12_object_level_authorization_and_cross_user_denial(api_client, standard_user, seed_roles, test_password):
    """Verify a user cannot modify another user's status or role."""
    other_user = User.objects.create_user(email="other@gqt.local", password=test_password)

    api_client.force_authenticate(user=standard_user)
    response = api_client.patch(
        f"/api/v1/auth/users/{other_user.id}/status/",
        {"is_active": False},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_13_unauthorized_role_escalation_prevention(api_client, standard_user):
    """Verify ordinary users cannot self-assign administrative roles."""
    api_client.force_authenticate(user=standard_user)
    response = api_client.post(
        f"/api/v1/auth/users/{standard_user.id}/roles/",
        {"role_codes": [RoleCatalog.ADMIN]},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_14_admin_can_safely_assign_roles(api_client, admin_user, standard_user):
    """Verify Administrator can assign valid operational roles."""
    api_client.force_authenticate(user=admin_user)
    response = api_client.post(
        f"/api/v1/auth/users/{standard_user.id}/roles/",
        {"role_codes": [RoleCatalog.STUDENT, RoleCatalog.TRAINER]},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert RoleCatalog.TRAINER in response.data["roles"]


# ==============================================================================
# Step 5: Password Management, Reset & Throttling Tests (15-18)
# ==============================================================================

@pytest.mark.django_db
def test_15_password_change_requires_current_password(api_client, standard_user, test_password):
    """Verify changing password verifies current credentials and enforces complexity."""
    api_client.force_authenticate(user=standard_user)

    # Wrong current password fails
    bad_resp = api_client.post(
        "/api/v1/auth/password/change/",
        {
            "current_password": "WrongPassword!",
            "new_password": "BrandNewPassword123!",
            "new_password_confirm": "BrandNewPassword123!",
        },
        format="json",
    )
    assert bad_resp.status_code == status.HTTP_400_BAD_REQUEST

    # Correct current password succeeds
    good_resp = api_client.post(
        "/api/v1/auth/password/change/",
        {
            "current_password": test_password,
            "new_password": "BrandNewPassword123!",
            "new_password_confirm": "BrandNewPassword123!",
        },
        format="json",
    )
    assert good_resp.status_code == status.HTTP_200_OK

    standard_user.refresh_from_db()
    assert standard_user.check_password("BrandNewPassword123!") is True


@pytest.mark.django_db
def test_16_password_reset_request_privacy(api_client, standard_user):
    """Verify reset request returns identical response for existing and non-existing emails."""
    resp1 = api_client.post(
        "/api/v1/auth/password/reset/request/",
        {"email": standard_user.email},
        format="json",
    )
    resp2 = api_client.post(
        "/api/v1/auth/password/reset/request/",
        {"email": "nonexistent@gqt.local"},
        format="json",
    )
    assert resp1.status_code == status.HTTP_200_OK
    assert resp2.status_code == status.HTTP_200_OK
    assert resp1.data == resp2.data


@pytest.mark.django_db
def test_17_password_reset_confirm_single_use(api_client, standard_user):
    """Verify reset token allows changing password and cannot be reused."""
    uid = urlsafe_base64_encode(force_bytes(standard_user.pk))
    token = default_token_generator.make_token(standard_user)

    confirm_resp = api_client.post(
        "/api/v1/auth/password/reset/confirm/",
        {
            "uidb64": uid,
            "token": token,
            "new_password": "CompletelyNewPass999!",
            "new_password_confirm": "CompletelyNewPass999!",
        },
        format="json",
    )
    assert confirm_resp.status_code == status.HTTP_200_OK

    # Reusing the same token must fail
    reuse_resp = api_client.post(
        "/api/v1/auth/password/reset/confirm/",
        {
            "uidb64": uid,
            "token": token,
            "new_password": "AnotherNewPass123!",
            "new_password_confirm": "AnotherNewPass123!",
        },
        format="json",
    )
    assert reuse_resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_18_login_throttling_scope_configured():
    """Verify rate-limiting throttle classes and auth scope are properly assigned."""
    from apps.accounts.throttles import AuthRateThrottle
    from apps.accounts.views import LoginView, PasswordResetRequestView
    from config.settings import base

    assert AuthRateThrottle.scope == "auth"
    assert AuthRateThrottle in LoginView.throttle_classes
    assert AuthRateThrottle in PasswordResetRequestView.throttle_classes
    assert "auth" in base.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]


# ==============================================================================
# Step 6: Bootstrap Admin & Safeguards (19-20)
# ==============================================================================

@pytest.mark.django_db
def test_19_bootstrap_admin_management_command_safeguards():
    """Verify bootstrap_admin rejects weak passwords and provisions admin safely."""
    # Weak password fails
    with pytest.raises(Exception):
        call_command("bootstrap_admin", email="admin2@gqt.local", password="short", no_input=True)

    # Strong password succeeds
    call_command(
        "bootstrap_admin",
        email="bootstrapped.admin@gqt.local",
        password="VeryStrongPassword!987",
        first_name="Root",
        last_name="Admin",
        no_input=True,
    )

    admin = User.objects.get(email="bootstrapped.admin@gqt.local")
    assert admin.is_superuser is True
    assert admin.is_staff is True
    assert admin.has_role(RoleCatalog.ADMIN) is True


@pytest.mark.django_db
def test_20_audit_event_creation_and_secret_redaction(api_client, standard_user, test_password):
    """Verify security actions produce audit events and never log passwords or tokens."""
    api_client.post(
        "/api/v1/auth/login/",
        {"email": standard_user.email, "password": test_password},
        format="json",
    )

    log_entry = AuditLog.objects.filter(
        resource_id=str(standard_user.id), action="LOGIN_SUCCESS"
    ).first()
    assert log_entry is not None
    # Verify no credentials leaked into changes dictionary
    assert test_password not in str(log_entry.changes)
    assert "password" not in log_entry.changes


# ==============================================================================
# Step 8 & 9: Cookie Auth, Rotation & OpenApi Verification (21-24)
# ==============================================================================

@pytest.mark.django_db
def test_21_cookie_based_authentication_request_flow(api_client, standard_user, test_password):
    """Verify HttpOnlyCookieJWTAuthentication successfully authenticates requests via cookie."""
    login_resp = api_client.post(
        "/api/v1/auth/login/",
        {"email": standard_user.email, "password": test_password},
        format="json",
    )
    access_token = login_resp.cookies[settings.JWT_AUTH_COOKIE].value

    # Make request with cookie injected
    client = APIClient()
    client.cookies[settings.JWT_AUTH_COOKIE] = access_token
    me_resp = client.get("/api/v1/auth/me/")
    assert me_resp.status_code == status.HTTP_200_OK
    assert me_resp.data["email"] == standard_user.email


@pytest.mark.django_db
def test_22_refresh_token_rotation_and_replay_detection(api_client, standard_user, test_password):
    """Verify refresh token rotation and replay prevention."""
    login_resp = api_client.post(
        "/api/v1/auth/login/",
        {"email": standard_user.email, "password": test_password},
        format="json",
    )
    refresh_1 = login_resp.data["tokens"]["refresh"]

    # First rotation succeeds
    rot_resp1 = api_client.post(
        "/api/v1/auth/refresh/",
        {"refresh": refresh_1},
        format="json",
    )
    assert rot_resp1.status_code == status.HTTP_200_OK
    refresh_2 = rot_resp1.data["refresh"]

    # Replaying refresh_1 must be rejected
    replay_resp = api_client.post(
        "/api/v1/auth/refresh/",
        {"refresh": refresh_1},
        format="json",
    )
    assert replay_resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_23_openapi_schema_contains_auth_endpoints(api_client):
    """Verify OpenAPI schema includes all new auth endpoints."""
    response = api_client.get("/api/v1/schema/")
    assert response.status_code == status.HTTP_200_OK
    content = response.content.decode()
    assert "/api/v1/auth/login/" in content
    assert "/api/v1/auth/logout/" in content
    assert "/api/v1/auth/me/" in content


@pytest.mark.django_db
def test_24_account_deactivation_prevents_active_sessions(api_client, standard_user, admin_user, test_password):
    """Verify deactivating an account immediately blocks subsequent authenticated requests."""
    login_resp = api_client.post(
        "/api/v1/auth/login/",
        {"email": standard_user.email, "password": test_password},
        format="json",
    )
    access_token = login_resp.data["tokens"]["access"]

    # Access is initially granted
    authed_client = APIClient()
    authed_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    assert authed_client.get("/api/v1/auth/me/").status_code == status.HTTP_200_OK

    # Admin deactivates student
    api_client.force_authenticate(user=admin_user)
    deactivate_resp = api_client.patch(
        f"/api/v1/auth/users/{standard_user.id}/status/",
        {"is_active": False},
        format="json",
    )
    assert deactivate_resp.status_code == status.HTTP_200_OK

    # Previous token is now rejected because account is inactive
    blocked_resp = authed_client.get("/api/v1/auth/me/")
    assert blocked_resp.status_code == status.HTTP_401_UNAUTHORIZED
