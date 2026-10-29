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
from rest_framework import exceptions, status
from rest_framework.test import APIClient
from apps.accounts.models import Role, RoleCatalog, UserRoleAssignment
from apps.accounts.services import assign_roles_to_user, update_user_status
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


# ==============================================================================
# Step 6: Phase 15 Workstream 2 User & Role Administration Tests (25-31)
# ==============================================================================

@pytest.mark.django_db
def test_25_admin_users_list_search_filter_and_ordering(api_client, admin_user, seed_roles, test_password):
    """Verify admin can list users with server-side search, role filter, status filter, and ordering."""
    u1 = User.objects.create_user(
        email="alice.trainer@gqt.local",
        password=test_password,
        first_name="Alice",
        last_name="Trainer",
        is_active=True,
    )
    assign_roles_to_user(u1, [RoleCatalog.TRAINER])

    u2 = User.objects.create_user(
        email="bob.inactive@gqt.local",
        password=test_password,
        first_name="Bob",
        last_name="Inactive",
        is_active=False,
    )
    assign_roles_to_user(u2, [RoleCatalog.STUDENT])

    api_client.force_authenticate(user=admin_user)

    # 1. Base list
    resp = api_client.get("/api/v1/auth/users/")
    assert resp.status_code == status.HTTP_200_OK
    assert "data" in resp.data
    emails = [item["email"] for item in resp.data["data"]]
    assert "alice.trainer@gqt.local" in emails
    assert "bob.inactive@gqt.local" in emails

    # 2. Search by name
    search_resp = api_client.get("/api/v1/auth/users/?search=Alice")
    assert search_resp.status_code == status.HTTP_200_OK
    search_emails = [item["email"] for item in search_resp.data["data"]]
    assert "alice.trainer@gqt.local" in search_emails
    assert "bob.inactive@gqt.local" not in search_emails

    # 3. Filter by role
    role_resp = api_client.get(f"/api/v1/auth/users/?role={RoleCatalog.TRAINER}")
    assert role_resp.status_code == status.HTTP_200_OK
    role_emails = [item["email"] for item in role_resp.data["data"]]
    assert "alice.trainer@gqt.local" in role_emails
    assert "bob.inactive@gqt.local" not in role_emails

    # 4. Filter by status
    status_resp = api_client.get("/api/v1/auth/users/?status=inactive")
    assert status_resp.status_code == status.HTTP_200_OK
    status_emails = [item["email"] for item in status_resp.data["data"]]
    assert "bob.inactive@gqt.local" in status_emails
    assert "alice.trainer@gqt.local" not in status_emails


@pytest.mark.django_db
def test_26_admin_update_permitted_profile_fields(api_client, admin_user, standard_user):
    """Verify administrator can update permitted user profile fields and generate an audit log."""
    api_client.force_authenticate(user=admin_user)

    payload = {
        "first_name": "Janet",
        "last_name": "Williams",
        "phone_number": "+91 99999 11111",
    }
    resp = api_client.patch(
        f"/api/v1/auth/users/{standard_user.id}/",
        payload,
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["first_name"] == "Janet"
    assert resp.data["last_name"] == "Williams"
    assert resp.data["phone_number"] == "+91 99999 11111"

    standard_user.refresh_from_db()
    assert standard_user.first_name == "Janet"
    assert standard_user.last_name == "Williams"
    assert standard_user.phone_number == "+91 99999 11111"

    # Verify audit event
    audit = AuditLog.objects.filter(
        resource_type="accounts.User",
        resource_id=str(standard_user.id),
        action="USER_PROFILE_UPDATED",
    ).first()
    assert audit is not None
    assert audit.user == admin_user
    assert "first_name" in audit.changes


@pytest.mark.django_db
def test_27_admin_update_protected_fields_rejected(api_client, admin_user, standard_user, test_password):
    """Verify protected fields (email, is_staff, is_superuser, password) cannot be altered via user profile update."""
    api_client.force_authenticate(user=admin_user)

    original_email = standard_user.email
    original_password_hash = standard_user.password

    resp = api_client.patch(
        f"/api/v1/auth/users/{standard_user.id}/",
        {
            "email": "hacked@gqt.local",
            "is_staff": True,
            "is_superuser": True,
            "password": "NewSecretPassword123!",
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK

    standard_user.refresh_from_db()
    assert standard_user.email == original_email
    assert standard_user.is_staff is False
    assert standard_user.is_superuser is False
    assert standard_user.password == original_password_hash


@pytest.mark.django_db
def test_28_admin_provision_user_with_roles_and_audit(api_client, admin_user, seed_roles, test_password):
    """Verify administrator can provision a new account with hashed password, assigned roles, and audit trail."""
    api_client.force_authenticate(user=admin_user)

    payload = {
        "email": "New.Trainer@gqt.local",
        "password": test_password,
        "first_name": "Suresh",
        "last_name": "Rao",
        "phone_number": "+91 91234 56789",
        "roles": [RoleCatalog.TRAINER, RoleCatalog.EVALUATOR],
    }
    resp = api_client.post(
        "/api/v1/auth/users/",
        payload,
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.data["email"] == "new.trainer@gqt.local"
    assert "password" not in resp.data
    assert RoleCatalog.TRAINER in resp.data["roles"]
    assert RoleCatalog.EVALUATOR in resp.data["roles"]

    # Verify user exists in DB with hashed password
    new_user = User.objects.get(email="new.trainer@gqt.local")
    assert new_user.check_password(test_password)
    assert not new_user.password.startswith("P@ss")

    # Verify duplicate creation is rejected
    dup_resp = api_client.post(
        "/api/v1/auth/users/",
        payload,
        format="json",
    )
    assert dup_resp.status_code == status.HTTP_400_BAD_REQUEST

    # Verify audit event
    audit = AuditLog.objects.filter(
        resource_type="accounts.User",
        resource_id=str(new_user.id),
        action="USER_CREATED",
    ).first()
    assert audit is not None
    assert audit.user == admin_user


@pytest.mark.django_db
def test_29_self_demotion_and_last_admin_protection(api_client, admin_user, seed_roles, test_password):
    """Verify self-demotion from ADMIN role is prevented, and deactivating the last admin is rejected."""
    api_client.force_authenticate(user=admin_user)

    # 1. Admin trying to revoke ADMIN role from themselves
    self_demote_resp = api_client.post(
        f"/api/v1/auth/users/{admin_user.id}/roles/",
        {"role_codes": [RoleCatalog.STUDENT]},
        format="json",
    )
    assert self_demote_resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot revoke the ADMIN role from their own account" in str(self_demote_resp.data)

    # 2. Admin trying to deactivate their own account
    self_deactivate_resp = api_client.patch(
        f"/api/v1/auth/users/{admin_user.id}/status/",
        {"is_active": False},
        format="json",
    )
    assert self_deactivate_resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Administrators cannot deactivate their own account" in str(self_deactivate_resp.data)

    # 3. Create a second admin
    second_admin = User.objects.create_user(
        email="admin2@gqt.local",
        password=test_password,
        is_active=True,
    )
    assign_roles_to_user(second_admin, [RoleCatalog.ADMIN])

    # Deactivating second admin works while admin_user is still active
    deactivate_sec_resp = api_client.patch(
        f"/api/v1/auth/users/{second_admin.id}/status/",
        {"is_active": False},
        format="json",
    )
    assert deactivate_sec_resp.status_code == status.HTTP_200_OK

    # Now make admin_user inactive directly in DB to test last admin check on second_admin
    admin_user.is_active = False
    admin_user.save()
    second_admin.is_active = True
    second_admin.save()

    # Re-authenticate as second_admin
    api_client.force_authenticate(user=second_admin)

    # Revoking ADMIN from second_admin when admin_user is inactive must fail (last admin)
    last_admin_role_resp = api_client.post(
        f"/api/v1/auth/users/{second_admin.id}/roles/",
        {"role_codes": [RoleCatalog.STUDENT]},
        format="json",
    )
    assert last_admin_role_resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_30_audit_logs_endpoint_returns_history_with_redacted_secrets(api_client, admin_user, standard_user):
    """Verify administrator can retrieve audit logs for a user and secrets are redacted."""
    # Emit an audit log with sensitive payload
    AuditLog.objects.create(
        user=admin_user,
        action="USER_CREDENTIAL_CHANGE",
        resource_type="accounts.User",
        resource_id=str(standard_user.id),
        changes={"password": "raw_secret_value", "first_name": "Jane"},
    )

    api_client.force_authenticate(user=admin_user)
    resp = api_client.get(f"/api/v1/auth/users/{standard_user.id}/audit-logs/")
    assert resp.status_code == status.HTTP_200_OK
    assert "data" in resp.data

    items = resp.data["data"]
    assert len(items) >= 1
    sample = next(item for item in items if item["action"] == "USER_CREDENTIAL_CHANGE")
    assert sample["actor_email"] == admin_user.email
    assert sample["changes"]["password"] == "[REDACTED]"
    assert sample["changes"]["first_name"] == "Jane"


@pytest.mark.django_db
def test_31_non_admin_cannot_access_user_management_endpoints(api_client, standard_user, placement_head_user, test_password):
    """Verify student and non-admin staff roles cannot access user management endpoints."""
    # Student forbidden
    api_client.force_authenticate(user=standard_user)
    assert api_client.get("/api/v1/auth/users/").status_code == status.HTTP_403_FORBIDDEN
    assert api_client.post("/api/v1/auth/users/", {"email": "x@gqt.local", "password": test_password}).status_code == status.HTTP_403_FORBIDDEN
    assert api_client.patch(f"/api/v1/auth/users/{standard_user.id}/", {"first_name": "X"}).status_code == status.HTTP_403_FORBIDDEN
    assert api_client.get(f"/api/v1/auth/users/{standard_user.id}/audit-logs/").status_code == status.HTTP_403_FORBIDDEN

    # Placement Head forbidden
    api_client.force_authenticate(user=placement_head_user)
    assert api_client.get("/api/v1/auth/users/").status_code == status.HTTP_403_FORBIDDEN
    assert api_client.post(f"/api/v1/auth/users/{standard_user.id}/roles/", {"role_codes": [RoleCatalog.ADMIN]}).status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_32_recursive_audit_log_redaction(api_client, admin_user, standard_user):
    """Verify recursive redaction handles arbitrary nested dictionaries, lists, and sensitive tokens."""
    nested_changes = {
        "user_profile": {
            "name": "Jane",
            "security": {
                "auth_token": "super_secret_token",
                "refresh_token": "refresh_12345",
                "password_hash": "pbkdf2_sha256$600000$...",
            },
        },
        "integrations": [
            {"service": "whatsapp", "api_key": "wa_key_secret_val"},
            {"service": "email", "secret": "smtp_pass_val"},
        ],
        "sensitive_tokens": ["token1", "token2"],
        "safe_list": ["item1", "item2"],
    }

    AuditLog.objects.create(
        user=admin_user,
        action="DEEP_SECURITY_AUDIT",
        resource_type="accounts.User",
        resource_id=str(standard_user.id),
        changes=nested_changes,
    )

    api_client.force_authenticate(user=admin_user)
    resp = api_client.get(f"/api/v1/auth/users/{standard_user.id}/audit-logs/")
    assert resp.status_code == status.HTTP_200_OK
    audit_entry = next(item for item in resp.data["data"] if item["action"] == "DEEP_SECURITY_AUDIT")
    changes = audit_entry["changes"]

    # Verify nested dictionary redaction
    assert changes["user_profile"]["name"] == "Jane"
    assert changes["user_profile"]["security"]["auth_token"] == "[REDACTED]"
    assert changes["user_profile"]["security"]["refresh_token"] == "[REDACTED]"
    assert changes["user_profile"]["security"]["password_hash"] == "[REDACTED]"

    # Verify nested list of dictionaries redaction
    assert changes["integrations"][0]["service"] == "whatsapp"
    assert changes["integrations"][0]["api_key"] == "[REDACTED]"
    assert changes["integrations"][1]["service"] == "email"
    assert changes["integrations"][1]["secret"] == "[REDACTED]"

    # Verify sensitive array key itself is redacted
    assert changes["sensitive_tokens"] == "[REDACTED]"

    # Verify non-sensitive elements preserved
    assert changes["safe_list"] == ["item1", "item2"]


@pytest.mark.django_db
def test_33_inactive_role_definition_cannot_satisfy_last_admin_requirement(api_client, admin_user, seed_roles, test_password):
    """Verify that an inactive ADMIN role definition or inactive assignment does not count as active administrator privilege."""
    admin_role = Role.objects.get(code=RoleCatalog.ADMIN)

    # Create user B with an admin assignment
    user_b = User.objects.create_user(
        email="admin_b@gqt.local",
        password=test_password,
        is_active=True,
    )
    assign_roles_to_user(user_b, [RoleCatalog.ADMIN])

    # Now simulate the ADMIN role being deactivated globally
    admin_role.is_active = False
    admin_role.save()

    # User B should not be counted as a valid active administrator
    api_client.force_authenticate(user=admin_user)
    # Attempting to deactivate admin_user or revoke admin from admin_user should fail because user_b's role is inactive
    with pytest.raises(exceptions.ValidationError) as exc:
        update_user_status(target_user=admin_user, is_active=False, updated_by=user_b)
    assert "Cannot deactivate the final active system administrator" in str(exc.value)


