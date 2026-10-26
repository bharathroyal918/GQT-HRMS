"""Role-based access control and object-level permission classes for Creative Studio (Phase 4)."""
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView
from apps.accounts.models import RoleCatalog


class IsCreativeStaffOrAuditor(permissions.BasePermission):
    """Allows operational staff and auditors to view creative requests;

    restricts mutations to authorized staff (Auditors are strictly read-only).
    Students, trainers, and evaluators are strictly denied.
    """

    message = "You do not have authorization to access Creative Studio records."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        user_roles = set(request.user.get_active_roles())

        # Unrelated or student roles are denied
        disallowed_roles = {RoleCatalog.STUDENT, RoleCatalog.TRAINER, RoleCatalog.EVALUATOR}
        if user_roles.issubset(disallowed_roles):
            self.message = "Students, trainers, and evaluators do not have access to internal creative workflows."
            return False

        # Auditor is read-only
        if RoleCatalog.AUDITOR in user_roles and not (
            user_roles & {
                RoleCatalog.ADMIN,
                RoleCatalog.PLACEMENT_HEAD,
                RoleCatalog.PLACEMENT_OFFICER,
                RoleCatalog.CREATIVE_DESIGNER,
            }
        ):
            if request.method in permissions.SAFE_METHODS:
                return True
            self.message = "Auditors hold read-only privileges and cannot modify creative assets."
            return False

        # Staff roles
        authorized_roles = {
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.CREATIVE_DESIGNER,
            RoleCatalog.AUDITOR,
        }
        return bool(user_roles & authorized_roles)


class CanAssignDesigner(permissions.BasePermission):
    """Restricts designer assignment to Placement Officers, Placement Heads, and Admins."""

    message = "Only Placement Officers, Placement Heads, or Admins can assign graphic designers."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_any_role(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        )


class CanVerifyCreativeChecklist(permissions.BasePermission):
    """Restricts Step 9 checklist item verification to Placement Officers, Placement Heads, and Admins."""

    message = "Only Placement Officers, Placement Heads, or Admins can verify creative design checklist items."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_any_role(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        )


class CanApproveCreative(permissions.BasePermission):
    """Restricts Step 9 final creative sign-off strictly to Placement Head or Admin."""

    message = "Only the Placement Head or System Administrator can approve creative promotional assets."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_any_role(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
        )
