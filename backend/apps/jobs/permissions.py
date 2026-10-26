"""Permission classes for Phase 3 Job Intake & Verification Checklist.

Enforces role boundaries from docs/security/role_permission_matrix.md:
- ADMIN: Full administrative control (intake, verification, approval, reopening).
- PLACEMENT_HEAD: Oversight, return for correction, checklist review, and internal approval sign-off.
- PLACEMENT_OFFICER: Corporate job intake, checklist verification, submission for approval.
- HR_RELATIONSHIP_MGR: Read-only access to view job requirements of corporate partners.
- CREATIVE_DESIGNER: Read-only access to approved job descriptions for creative design preparation.
- AUDITOR: Strictly read-only access (SAFE_METHODS) across all job and checklist endpoints.
- STUDENT, TRAINER, EVALUATOR: Strictly denied access (403 Forbidden).
"""
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView
from apps.accounts.models import RoleCatalog

# Roles permitted to create, edit drafts, and submit jobs for verification
JOB_INTAKE_ROLES = (
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
)

# Roles permitted to verify checklist items (Step 6)
CHECKLIST_VERIFIER_ROLES = (
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
)

# Roles permitted to approve or reject job requirements (Step 7)
JOB_APPROVER_ROLES = (
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
)

# Roles with read privileges on job directory
JOB_READ_ROLES = (
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.HR_RELATIONSHIP_MGR,
    RoleCatalog.CREATIVE_DESIGNER,
    RoleCatalog.AUDITOR,
)


class IsJobStaffOrAuditor(permissions.BasePermission):
    """Enforces job requirement directory and detail access.

    - Authenticated users holding staff roles may read.
    - Creators and placement staff may create and update editable drafts.
    - Auditors hold strictly read-only access.
    - Students, trainers, and evaluators are strictly denied.
    """

    message = "You do not have authorization to access Job Requirement records."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_superuser:
            return True

        # Safe read-only methods
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_any_role(*JOB_READ_ROLES)

        # Mutating methods (POST, PUT, PATCH, DELETE) require intake staff roles
        if request.user.has_role(RoleCatalog.AUDITOR):
            self.message = "Auditors hold read-only privileges and cannot modify job records."
            return False

        return request.user.has_any_role(*JOB_INTAKE_ROLES)

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return request.user.has_any_role(*JOB_READ_ROLES)

        if request.user.has_role(RoleCatalog.AUDITOR):
            return False

        return request.user.has_any_role(*JOB_INTAKE_ROLES)


class CanVerifyJobChecklist(permissions.BasePermission):
    """Restricts verification of individual checklist items to Placement Officers, Placement Heads, and Admins."""

    message = "Only Placement Officers, Placement Heads, or Admins may verify checklist items."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return request.user.has_any_role(*JOB_READ_ROLES)

        return request.user.has_any_role(*CHECKLIST_VERIFIER_ROLES)


class CanApproveJobRequirement(permissions.BasePermission):
    """Strictly restricts final approval (Step 7) or formal rejection to Placement Head and Admin."""

    message = "Only the Placement Head or System Administrator is authorized to approve or reject opportunities."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False

        if request.user.is_superuser:
            return True

        return request.user.has_any_role(*JOB_APPROVER_ROLES)
