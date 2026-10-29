"""Selectors layer for Accounts, Identity, and Role-Based Access Control."""
from typing import Optional
from django.db.models import Prefetch, Q, QuerySet
from apps.accounts.models import Role, RoleCatalog, User, UserRoleAssignment
from apps.core.models import AuditLog

ALLOWED_USER_ORDERING_FIELDS = {
    "created_at",
    "-created_at",
    "email",
    "-email",
    "first_name",
    "-first_name",
    "last_name",
    "-last_name",
    "last_login",
    "-last_login",
}


def get_admin_users_queryset(
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    ordering: Optional[str] = None,
) -> QuerySet[User]:
    """Retrieve an optimized queryset of user accounts with server-side search, filtering, and ordering."""
    active_assignments_prefetch = Prefetch(
        "role_assignments",
        queryset=UserRoleAssignment.objects.filter(
            is_active=True,
            role__is_active=True,
        ).select_related("role"),
    )

    qs = User.objects.all().prefetch_related(active_assignments_prefetch)

    # 1. Search across identifiers
    if search:
        search_term = search.strip()
        qs = qs.filter(
            Q(email__icontains=search_term)
            | Q(first_name__icontains=search_term)
            | Q(last_name__icontains=search_term)
            | Q(phone_number__icontains=search_term)
        )

    # 2. Filter by operational role
    if role:
        role_code = role.strip().upper()
        if role_code == RoleCatalog.ADMIN:
            # Superusers or users with active ADMIN assignment
            qs = qs.filter(
                Q(is_superuser=True)
                | Q(
                    role_assignments__role__code=RoleCatalog.ADMIN,
                    role_assignments__is_active=True,
                    role_assignments__role__is_active=True,
                )
            ).distinct()
        else:
            qs = qs.filter(
                role_assignments__role__code=role_code,
                role_assignments__is_active=True,
                role_assignments__role__is_active=True,
            ).distinct()

    # 3. Filter by account active status
    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    # 4. Sorting & Ordering
    if ordering and ordering in ALLOWED_USER_ORDERING_FIELDS:
        qs = qs.order_by(ordering)
    else:
        qs = qs.order_by("-created_at")

    return qs


def get_user_audit_logs(user: User) -> QuerySet[AuditLog]:
    """Retrieve immutable audit events relating to the specified user account."""
    return (
        AuditLog.objects.filter(
            resource_type="accounts.User",
            resource_id=str(user.id),
        )
        .select_related("user")
        .order_by("-created_at")
    )

