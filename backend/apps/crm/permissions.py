"""Permission classes for Phase 2 Corporate CRM & HR Directory."""
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView
from apps.accounts.models import RoleCatalog

CRM_MUTATING_ROLES = (
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.HR_RELATIONSHIP_MGR,
)

CRM_READ_ONLY_ROLES = (
    RoleCatalog.AUDITOR,
)

DENIED_ROLES = (
    RoleCatalog.STUDENT,
    RoleCatalog.CREATIVE_DESIGNER,
    RoleCatalog.TRAINER,
    RoleCatalog.EVALUATOR,
)


class IsCRMStaffOrAuditor(permissions.BasePermission):
    """Enforces CRM role-based access.

    - ADMIN, PLACEMENT_HEAD, PLACEMENT_OFFICER, HR_RELATIONSHIP_MGR have full operational access.
    - AUDITOR has strictly READ-ONLY (SAFE_METHODS) access.
    - STUDENT, CREATIVE_DESIGNER, TRAINER, EVALUATOR and unassigned users are denied (403 Forbidden).
    """

    message = "You do not have authorization to access Corporate CRM records."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_superuser:
            return True

        # Check explicit staff roles
        if request.user.has_any_role(*CRM_MUTATING_ROLES):
            return True

        # Check auditor read-only
        if request.user.has_role(RoleCatalog.AUDITOR):
            if request.method in permissions.SAFE_METHODS:
                return True
            self.message = "Auditors hold read-only privileges and cannot modify CRM records."
            return False

        # Any other role or no role is denied
        return False

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_superuser:
            return True

        if request.user.has_any_role(*CRM_MUTATING_ROLES):
            return True

        if request.user.has_role(RoleCatalog.AUDITOR):
            return request.method in permissions.SAFE_METHODS

        return False


class IsCRMManagerOrAdmin(permissions.BasePermission):
    """Restricted to ADMIN and PLACEMENT_HEAD for supervisory settings and reconciliation."""

    message = "Management authorization required for this CRM administrative operation."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        return (
            request.user.is_superuser
            or request.user.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD)
        )


class CanManageCRMReconciliation(permissions.BasePermission):
    """Authorizes viewing diagnostics (Staff + Auditor) and executing reconciliation (Staff only)."""

    message = "You do not have permission to manage CRM database reconciliation."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return request.user.has_any_role(
                RoleCatalog.ADMIN,
                RoleCatalog.PLACEMENT_HEAD,
                RoleCatalog.PLACEMENT_OFFICER,
                RoleCatalog.AUDITOR,
            )

        # Mutating operations (POST sync)
        if request.user.has_role(RoleCatalog.AUDITOR):
            self.message = "Auditors hold read-only privileges and cannot execute database reconciliation."
            return False

        return request.user.has_any_role(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        )


class CanAccessStudent360(permissions.BasePermission):
    """Ensures staff and auditors can inspect any student 360 profile, while students can only view their own."""

    message = "You do not have authorization to view this candidate 360 profile."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_superuser:
            return True

        return request.user.has_any_role(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.AUDITOR,
            RoleCatalog.HR_RELATIONSHIP_MGR,
            RoleCatalog.TRAINER,
            RoleCatalog.STUDENT,
        )

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_superuser:
            return True

        if request.user.has_any_role(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.AUDITOR,
            RoleCatalog.HR_RELATIONSHIP_MGR,
            RoleCatalog.TRAINER,
        ):
            return True

        # Student ownership check
        student_user_id = getattr(obj, "user_id", None) or (obj.get("student", {}).get("user_id") if isinstance(obj, dict) else None)
        if not student_user_id and hasattr(obj, "user"):
            student_user_id = obj.user.id
        return student_user_id == request.user.id

