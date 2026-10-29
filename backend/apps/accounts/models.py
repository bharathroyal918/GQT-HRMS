"""Accounts, Identity, and Role-Based Access Control (RBAC) Models."""
import uuid
from typing import List
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.db.models.functions import Lower


class RoleCatalog:
    """Standardized operational role codes derived from the authoritative workflow."""

    ADMIN = "ADMIN"
    PLACEMENT_HEAD = "PLACEMENT_HEAD"
    PLACEMENT_OFFICER = "PLACEMENT_OFFICER"
    HR_RELATIONSHIP_MGR = "HR_RELATIONSHIP_MGR"
    CREATIVE_DESIGNER = "CREATIVE_DESIGNER"
    TRAINER = "TRAINER"
    EVALUATOR = "EVALUATOR"
    STUDENT = "STUDENT"
    AUDITOR = "AUDITOR"

    CHOICES = (
        (ADMIN, "System Administrator"),
        (PLACEMENT_HEAD, "Placement Head / Director"),
        (PLACEMENT_OFFICER, "Placement Officer / Executive"),
        (HR_RELATIONSHIP_MGR, "Corporate CRM & HR Relationship Manager"),
        (CREATIVE_DESIGNER, "Recruitment Creative Designer"),
        (TRAINER, "Placement & Technical Trainer"),
        (EVALUATOR, "Mock Interview Evaluator"),
        (STUDENT, "Enrolled Student / Candidate"),
        (AUDITOR, "Compliance & Audit Officer"),
    )


class UserManager(BaseUserManager):
    """Custom manager for email-based authentication and user lifecycle."""

    def normalize_email(self, email: str | None) -> str:
        """Case-insensitively normalize and lowercase the email address."""
        email = super().normalize_email(email or "")
        return email.lower().strip()

    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        """Create and persist a regular user with a normalized email and hashed password."""
        if not email:
            raise ValueError("An email address is required to register an account.")

        normalized_email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=normalized_email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        """Create and persist an administrator with superuser and staff flags."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser accounts must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser accounts must have is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with UUID primary key and normalized email as the authentication identity."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Cryptographically random UUIDv4 primary key.",
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Normalized email address used as the primary login identifier.",
    )
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    phone_number = models.CharField(max_length=20, blank=True, default="")

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Designates whether this user account is active and permitted to authenticate.",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into Django admin.",
    )
    is_superuser = models.BooleanField(
        default=False,
        help_text="Designates that this user has all permissions without explicitly assigning them.",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: List[str] = []

    class Meta:
        db_table = "accounts_user"
        ordering = ["-created_at"]
        verbose_name = "User Account"
        verbose_name_plural = "User Accounts"
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="unique_lower_email_user",
            ),
        ]

    def __str__(self) -> str:
        return self.email

    def clean(self) -> None:
        """Ensure email is consistently normalized and lowercased before saving."""
        super().clean()
        if self.email:
            self.email = self.email.lower().strip()

    @property
    def full_name(self) -> str:
        """Compute human-friendly full name with safe fallback to email username."""
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email.split("@")[0]

    def get_active_roles(self) -> List[str]:
        """Return the list of unique role codes actively assigned to this user."""
        if self.is_superuser:
            return [RoleCatalog.ADMIN]
        if hasattr(self, "_prefetched_objects_cache") and "role_assignments" in self._prefetched_objects_cache:
            return sorted(list({
                ra.role.code for ra in self.role_assignments.all()
                if ra.is_active and ra.role.is_active
            }))
        return list(
            self.role_assignments.filter(is_active=True, role__is_active=True)
            .values_list("role__code", flat=True)
            .distinct()
        )

    def has_role(self, role_code: str) -> bool:
        """Check whether user holds an active role assignment or is a superuser."""
        if self.is_superuser:
            return True
        return self.role_assignments.filter(
            is_active=True, role__code=role_code, role__is_active=True
        ).exists()

    def has_any_role(self, *role_codes: str) -> bool:
        """Check whether user holds any of the specified roles."""
        if self.is_superuser:
            return True
        return self.role_assignments.filter(
            is_active=True, role__code__in=role_codes, role__is_active=True
        ).exists()


class Role(models.Model):
    """Normalized catalog of operational roles with strict role codes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Machine-readable immutable role code (e.g., PLACEMENT_HEAD).",
    )
    name = models.CharField(max_length=100, help_text="Human-readable role title.")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_role"
        ordering = ["code"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class UserRoleAssignment(models.Model):
    """Relational assignment mapping users to roles with status and assignment audit metadata."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="user_assignments",
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_roles_audit",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Allows disabling a role assignment without destroying historical records.",
    )

    class Meta:
        db_table = "accounts_user_role_assignment"
        ordering = ["-assigned_at"]
        verbose_name = "User Role Assignment"
        verbose_name_plural = "User Role Assignments"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="unique_user_role_assignment",
            ),
        ]

    def __str__(self) -> str:
        status = "Active" if self.is_active else "Inactive"
        return f"{self.user.email} -> {self.role.code} ({status})"
