"""Comprehensive test suite for Phase 4: Creative Studio & Promotional Assets Management (Workflow Steps 8–9)."""
from datetime import timedelta
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import RoleCatalog
from apps.accounts.services import assign_roles_to_user
from apps.core.models import AuditLog
from apps.crm.models import Company, CompanyDomainCategory, HRContact
from apps.jobs.models import (
    JobRequirement,
    JobRequirementStatus,
    ChecklistItemStatus as JobCheckStatus,
)
from apps.creatives.models import (
    CreativeRequest,
    CreativeRequestStatus,
    CreativeDeliverableType,
    CreativePriority,
    CreativeAssetVersion,
    AssetVersionStatus,
    CreativeChecklistItem,
    ChecklistItemStatus,
    ChecklistItemCode,
    CreativeDecision,
)
from apps.creatives.services import (
    create_creative_request,
    update_creative_brief,
    assign_designer,
    upload_asset_version,
    verify_checklist_item,
    return_for_correction,
    approve_asset_version,
    reject_asset_version,
    archive_creative_request,
    restore_creative_request,
)
from apps.creatives.selectors import (
    get_creative_requests_queryset,
    get_creative_request_by_id,
    get_asset_version_by_id,
    get_designer_queue_queryset,
    get_pending_review_queue_queryset,
    get_creative_metrics,
)

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
def admin_user(db, seed_roles, test_password):
    user = User.objects.create_superuser(
        email="admin@gqt.local", password=test_password, first_name="Admin", last_name="User"
    )
    assign_roles_to_user(user, [RoleCatalog.ADMIN])
    return user


@pytest.fixture
def placement_head_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="head@gqt.local", password=test_password, first_name="Head", last_name="Director"
    )
    assign_roles_to_user(user, [RoleCatalog.PLACEMENT_HEAD])
    return user


@pytest.fixture
def placement_officer_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="officer@gqt.local", password=test_password, first_name="Officer", last_name="Executive"
    )
    assign_roles_to_user(user, [RoleCatalog.PLACEMENT_OFFICER])
    return user


@pytest.fixture
def designer_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="designer@gqt.local", password=test_password, first_name="Creative", last_name="Designer"
    )
    assign_roles_to_user(user, [RoleCatalog.CREATIVE_DESIGNER])
    return user


@pytest.fixture
def second_designer_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="designer2@gqt.local", password=test_password, first_name="Second", last_name="Designer"
    )
    assign_roles_to_user(user, [RoleCatalog.CREATIVE_DESIGNER])
    return user


@pytest.fixture
def auditor_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="auditor@gqt.local", password=test_password, first_name="Compliance", last_name="Auditor"
    )
    assign_roles_to_user(user, [RoleCatalog.AUDITOR])
    return user


@pytest.fixture
def student_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="student@gqt.local", password=test_password, first_name="Enrolled", last_name="Student"
    )
    assign_roles_to_user(user, [RoleCatalog.STUDENT])
    return user


@pytest.fixture
def sample_company(db, admin_user):
    return Company.objects.create(
        name="Infosys Limited",
        website="https://www.infosys.com",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        owner=admin_user,
    )


@pytest.fixture
def approved_job(db, admin_user, sample_company):
    now = timezone.now()
    job = JobRequirement.objects.create(
        company=sample_company,
        title="Systems Engineer 2026",
        job_description="Core engineering & software developer opportunity for campus freshers.",
        skills_required="Java, Python, SQL, Data Structures",
        min_salary=Decimal("4.50"),
        max_salary=Decimal("6.50"),
        location="Bengaluru / Mysore",
        eligibility_criteria="BE/B.Tech (CS, IS, EC) with 65%+ and zero active backlogs.",
        interview_date=now + timedelta(days=20),
        registration_deadline=now + timedelta(days=10),
        status=JobRequirementStatus.APPROVED,
        created_by=admin_user,
        approved_by=admin_user,
        approved_at=now,
    )
    return job


@pytest.fixture
def draft_job(db, admin_user, sample_company):
    now = timezone.now()
    return JobRequirement.objects.create(
        company=sample_company,
        title="Draft Trainee Role",
        job_description="Unapproved job description",
        skills_required="Python",
        location="Bengaluru",
        registration_deadline=now + timedelta(days=5),
        status=JobRequirementStatus.DRAFT,
        created_by=admin_user,
    )


@pytest.fixture
def valid_png_file():
    # 1000x1000 PNG image header with IHDR chunk
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x03\xe8\x00\x00\x03\xe8\x08\x06\x00\x00\x00\x1f\x15\xc4\x89" + b"\x00" * 100
    return SimpleUploadedFile("flyer.png", png_bytes, content_type="image/png")


@pytest.fixture
def valid_jpeg_file():
    # Valid JPEG image header
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xc0\x00\x11\x08\x03\xe8\x03\xe8\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01\xff\xd9"
    return SimpleUploadedFile("banner.jpg", jpeg_bytes, content_type="image/jpeg")


@pytest.fixture
def valid_pdf_file():
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
    return SimpleUploadedFile("flyer.pdf", pdf_bytes, content_type="application/pdf")


@pytest.fixture
def malicious_svg_file():
    svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert('XSS')</script></svg>"
    return SimpleUploadedFile("creative.svg", svg_bytes, content_type="image/svg+xml")


# ==============================================================================
# Domain Model & Service Tests (Steps 8–9)
# ==============================================================================

@pytest.mark.django_db
def test_01_create_creative_request_from_approved_job_success(approved_job, placement_officer_user, designer_user):
    """Step 8: Creative request creation links cleanly to approved JobRequirement."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys 2026 Campus Drive Flyer",
        deliverable_type=CreativeDeliverableType.FLYER,
        priority=CreativePriority.HIGH,
        assigned_designer=designer_user,
    )
    assert req.id is not None
    assert req.job_requirement_id == approved_job.id
    assert req.title == "Infosys 2026 Campus Drive Flyer"
    assert req.deliverable_type == CreativeDeliverableType.FLYER
    assert req.status == CreativeRequestStatus.ASSIGNED
    assert req.assigned_designer_id == designer_user.id
    assert "Infosys Limited" in req.brief
    assert "Systems Engineer 2026" in req.brief


@pytest.mark.django_db
def test_02_create_creative_request_from_unapproved_job_rejected(draft_job, placement_officer_user):
    """Step 8 Gating: Unapproved job requirements are strictly rejected."""
    with pytest.raises(ValidationError) as exc:
        create_creative_request(
            job_requirement=draft_job,
            user=placement_officer_user,
            title="Unapproved Job Creative",
        )
    assert "Creative requests can only be initiated for approved job requirements" in str(exc.value)


@pytest.mark.django_db
def test_03_duplicate_active_creative_request_for_same_deliverable_rejected(approved_job, placement_officer_user):
    """Step 8 Uniqueness: Prevents duplicate active requests for the exact same job and deliverable."""
    create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="First Flyer Request",
        deliverable_type=CreativeDeliverableType.FLYER,
    )

    with pytest.raises(ValidationError) as exc:
        create_creative_request(
            job_requirement=approved_job,
            user=placement_officer_user,
            title="Second Flyer Request",
            deliverable_type=CreativeDeliverableType.FLYER,
        )
    assert "An active creative request already exists" in str(exc.value)


@pytest.mark.django_db
def test_04_different_deliverable_types_for_same_job_allowed(approved_job, placement_officer_user):
    """Step 8 Deliverables: A job requirement can have distinct requests for Flyer, Banner, and Social Post."""
    req_flyer = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer",
        deliverable_type=CreativeDeliverableType.FLYER,
    )
    req_banner = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Banner",
        deliverable_type=CreativeDeliverableType.BANNER,
    )
    assert req_flyer.id != req_banner.id
    assert req_flyer.deliverable_type == CreativeDeliverableType.FLYER
    assert req_banner.deliverable_type == CreativeDeliverableType.BANNER


@pytest.mark.django_db
def test_05_assign_designer_lifecycle(approved_job, placement_officer_user, designer_user, second_designer_user):
    """Step 8 Designer Assignment: Assigns and reassigns graphic designers with audit trail."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Campaign",
    )
    assert req.status == CreativeRequestStatus.DRAFT
    assert req.assigned_designer is None

    # Assign designer
    assign_designer(req, designer_user, assigned_by=placement_officer_user)
    req.refresh_from_db()
    assert req.assigned_designer_id == designer_user.id
    assert req.status == CreativeRequestStatus.ASSIGNED

    # Reassign designer
    assign_designer(req, second_designer_user, assigned_by=placement_officer_user)
    req.refresh_from_db()
    assert req.assigned_designer_id == second_designer_user.id


@pytest.mark.django_db
def test_06_assign_non_designer_role_rejected(approved_job, placement_officer_user, student_user):
    """Step 8 Security: Assigning a user without CREATIVE_DESIGNER role is rejected."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Campaign",
    )
    with pytest.raises(ValidationError) as exc:
        assign_designer(req, student_user, assigned_by=placement_officer_user)
    assert "does not hold the CREATIVE_DESIGNER role" in str(exc.value)


@pytest.mark.django_db
def test_07_upload_asset_version_initializes_4point_checklist(approved_job, placement_officer_user, designer_user, valid_png_file):
    """Steps 8 & 9: Uploading a version auto-initializes the authoritative 4-point design verification checklist."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )

    version = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_png_file,
        designer_user=designer_user,
        designer_notes="Initial draft v1 matching brand specs.",
    )

    assert version.version_number == 1
    assert version.status == AssetVersionStatus.SUBMITTED
    assert version.file_name == "flyer.png"
    assert version.width_px == 1000
    assert version.height_px == 1000
    assert version.sha256_hash is not None

    req.refresh_from_db()
    assert req.status == CreativeRequestStatus.REVIEW_PENDING

    # Verify that exactly 4 checklist items were created
    items = version.checklist_items.all()
    assert items.count() == 4
    codes = set(items.values_list("item_code", flat=True))
    expected_codes = {
        ChecklistItemCode.FLYER_ACCURACY,
        ChecklistItemCode.OFFICIAL_LOGO,
        ChecklistItemCode.QR_CODE,
        ChecklistItemCode.REGISTRATION_LINK_AND_CONTACTS,
    }
    assert codes == expected_codes
    assert all(item.status == ChecklistItemStatus.PENDING for item in items)


@pytest.mark.django_db
def test_08_upload_svg_rejected_for_security(approved_job, placement_officer_user, designer_user, malicious_svg_file):
    """Security: SVG uploads are strictly rejected to prevent Stored XSS."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )

    with pytest.raises(ValidationError) as exc:
        upload_asset_version(
            creative_req=req,
            uploaded_file=malicious_svg_file,
            designer_user=designer_user,
        )
    assert "strictly prohibited for security reasons" in str(exc.value) or "SVGs and executable" in str(exc.value)


@pytest.mark.django_db
def test_09_monotonic_version_progression_and_preservation(approved_job, placement_officer_user, designer_user, valid_png_file, valid_jpeg_file):
    """Step 8 & 9: Multiple revisions receive monotonic version numbers (v1, v2) preserving earlier history."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )

    v1 = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_png_file,
        designer_user=designer_user,
        designer_notes="Version 1",
    )
    assert v1.version_number == 1

    v2 = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_jpeg_file,
        designer_user=designer_user,
        designer_notes="Version 2 with corrected logo",
    )
    assert v2.version_number == 2
    assert req.versions.count() == 2

    # Earlier version v1 still exists
    assert req.versions.filter(version_number=1).exists()


@pytest.mark.django_db
def test_10_verify_checklist_items_progression(approved_job, placement_officer_user, designer_user, valid_png_file):
    """Step 9: Verification progresses item status and advances version to IN_REVIEW."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )
    version = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_png_file,
        designer_user=designer_user,
    )

    # Verify first 2 criteria
    verify_checklist_item(
        version=version,
        item_code=ChecklistItemCode.FLYER_ACCURACY,
        status=ChecklistItemStatus.VERIFIED,
        reviewer=placement_officer_user,
        remarks="JD details match approved spec.",
    )
    verify_checklist_item(
        version=version,
        item_code=ChecklistItemCode.OFFICIAL_LOGO,
        status=ChecklistItemStatus.VERIFIED,
        reviewer=placement_officer_user,
        remarks="High-res corporate logo verified.",
    )

    version.refresh_from_db()
    assert version.status == AssetVersionStatus.IN_REVIEW
    assert not version.all_mandatory_verified
    assert version.checklist_progress["verified"] == 2
    assert version.checklist_progress["total"] == 4
    assert version.checklist_progress["percent"] == 50


@pytest.mark.django_db
def test_11_return_for_correction_lifecycle(approved_job, placement_officer_user, designer_user, valid_png_file):
    """Step 9: Incomplete or incorrect designs are returned to CHANGES_REQUESTED with mandatory feedback."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )
    version = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_png_file,
        designer_user=designer_user,
    )

    return_for_correction(
        version=version,
        reviewer=placement_officer_user,
        feedback="Registration QR code is blurry; please replace with high-contrast vector.",
    )

    version.refresh_from_db()
    req.refresh_from_db()
    assert version.status == AssetVersionStatus.CHANGES_REQUESTED
    assert req.status == CreativeRequestStatus.CHANGES_REQUESTED
    assert "Registration QR code is blurry" in version.rejection_reason


@pytest.mark.django_db
def test_12_approve_fails_if_checklist_incomplete(approved_job, placement_officer_user, placement_head_user, designer_user, valid_png_file):
    """Step 9 Gating: Placement Head approval fails if all 4 checklist points are not VERIFIED."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )
    version = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_png_file,
        designer_user=designer_user,
    )

    # Only verify 3 of 4 items
    verify_checklist_item(version, ChecklistItemCode.FLYER_ACCURACY, ChecklistItemStatus.VERIFIED, placement_officer_user)
    verify_checklist_item(version, ChecklistItemCode.OFFICIAL_LOGO, ChecklistItemStatus.VERIFIED, placement_officer_user)
    verify_checklist_item(version, ChecklistItemCode.QR_CODE, ChecklistItemStatus.VERIFIED, placement_officer_user)

    with pytest.raises(ValidationError) as exc:
        approve_asset_version(version, approver=placement_head_user)
    assert "All 4 mandatory verification checklist criteria must evaluate to VERIFIED" in str(exc.value)


@pytest.mark.django_db
def test_13_approve_succeeds_when_all_4_verified(approved_job, placement_officer_user, placement_head_user, designer_user, valid_png_file):
    """Step 9 Approval Gate: Placement Head approval succeeds when all 4 checklist points are VERIFIED."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )
    version = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_png_file,
        designer_user=designer_user,
    )

    # Verify all 4 items
    verify_checklist_item(version, ChecklistItemCode.FLYER_ACCURACY, ChecklistItemStatus.VERIFIED, placement_officer_user)
    verify_checklist_item(version, ChecklistItemCode.OFFICIAL_LOGO, ChecklistItemStatus.VERIFIED, placement_officer_user)
    verify_checklist_item(version, ChecklistItemCode.QR_CODE, ChecklistItemStatus.VERIFIED, placement_officer_user)
    verify_checklist_item(version, ChecklistItemCode.REGISTRATION_LINK_AND_CONTACTS, ChecklistItemStatus.VERIFIED, placement_officer_user)

    version.refresh_from_db()
    assert version.all_mandatory_verified

    approved_ver = approve_asset_version(version, approver=placement_head_user, comments="Ready for campus broadcast")
    assert approved_ver.is_approved is True
    assert approved_ver.status == AssetVersionStatus.APPROVED
    assert approved_ver.approved_by_id == placement_head_user.id

    req.refresh_from_db()
    assert req.status == CreativeRequestStatus.APPROVED
    assert req.is_locked is True


@pytest.mark.django_db
def test_14_placement_officer_cannot_approve_creative(approved_job, placement_officer_user, designer_user, valid_png_file):
    """Step 9 Authority: Placement Officers cannot bypass the Placement Head approval gate."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )
    version = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_png_file,
        designer_user=designer_user,
    )
    # Verify all items
    for item in version.checklist_items.all():
        verify_checklist_item(version, item.item_code, ChecklistItemStatus.VERIFIED, placement_officer_user)

    with pytest.raises(PermissionDenied) as exc:
        approve_asset_version(version, approver=placement_officer_user)
    assert "Only the Placement Head or System Administrator can approve creative promotional assets" in str(exc.value)


@pytest.mark.django_db
def test_15_reject_asset_version(approved_job, placement_officer_user, placement_head_user, designer_user, valid_png_file):
    """Step 9: Formally rejecting an asset version records rejection reason."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )
    version = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_png_file,
        designer_user=designer_user,
    )

    reject_asset_version(version, user=placement_head_user, rejection_reason="Company cancelled campus hiring drive")
    version.refresh_from_db()
    req.refresh_from_db()
    assert version.status == AssetVersionStatus.REJECTED
    assert req.status == CreativeRequestStatus.REJECTED
    assert "Company cancelled campus hiring drive" in version.rejection_reason


@pytest.mark.django_db
def test_16_approved_version_is_immutable(approved_job, placement_officer_user, placement_head_user, designer_user, valid_png_file):
    """Security & Immutability: Once approved, checklist items cannot be modified."""
    req = create_creative_request(
        job_requirement=approved_job,
        user=placement_officer_user,
        title="Infosys Flyer Pack",
        assigned_designer=designer_user,
    )
    version = upload_asset_version(
        creative_req=req,
        uploaded_file=valid_png_file,
        designer_user=designer_user,
    )
    for item in version.checklist_items.all():
        verify_checklist_item(version, item.item_code, ChecklistItemStatus.VERIFIED, placement_officer_user)

    approve_asset_version(version, approver=placement_head_user)

    with pytest.raises(ValidationError) as exc:
        verify_checklist_item(version, ChecklistItemCode.FLYER_ACCURACY, ChecklistItemStatus.REJECTED, placement_officer_user)
    assert "Cannot modify verification checklist of an already approved asset version" in str(exc.value)


# ==============================================================================
# API Endpoints & Role-Based Access Control Tests
# ==============================================================================

@pytest.mark.django_db
def test_17_api_list_creative_requests(api_client, approved_job, placement_officer_user):
    """API: Lists creative requests with search and pagination."""
    create_creative_request(approved_job, placement_officer_user, "Flyer for Infosys", CreativeDeliverableType.FLYER)
    create_creative_request(approved_job, placement_officer_user, "Banner for Infosys", CreativeDeliverableType.BANNER)

    api_client.force_authenticate(user=placement_officer_user)
    response = api_client.get("/api/v1/creatives/requests/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["meta"]["count"] == 2


@pytest.mark.django_db
def test_18_api_create_creative_request(api_client, approved_job, placement_officer_user, designer_user):
    """API: Create creative request endpoint."""
    api_client.force_authenticate(user=placement_officer_user)
    payload = {
        "job_requirement_id": str(approved_job.id),
        "title": "Infosys Social Media Campaign",
        "deliverable_type": CreativeDeliverableType.SOCIAL_POST,
        "priority": CreativePriority.URGENT,
        "assigned_designer_id": str(designer_user.id),
    }
    response = api_client.post("/api/v1/creatives/requests/", data=payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == "Infosys Social Media Campaign"
    assert response.data["status"] == CreativeRequestStatus.ASSIGNED


@pytest.mark.django_db
def test_19_api_assign_designer(api_client, approved_job, placement_officer_user, designer_user):
    """API: Assign designer endpoint."""
    req = create_creative_request(approved_job, placement_officer_user, "Flyer Campaign")
    api_client.force_authenticate(user=placement_officer_user)

    response = api_client.post(
        f"/api/v1/creatives/requests/{req.id}/assign/",
        data={"designer_id": str(designer_user.id)},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["assigned_designer"]["id"] == str(designer_user.id)


@pytest.mark.django_db
def test_20_api_verify_checklist_and_approve(api_client, approved_job, placement_officer_user, placement_head_user, designer_user, valid_png_file):
    """API: Full verification and approval flow."""
    req = create_creative_request(approved_job, placement_officer_user, "Infosys Flyer Pack", assigned_designer=designer_user)
    version = upload_asset_version(req, valid_png_file, designer_user)

    # 1. Verify all 4 checklist points as Placement Officer
    api_client.force_authenticate(user=placement_officer_user)
    for item_code in [
        ChecklistItemCode.FLYER_ACCURACY,
        ChecklistItemCode.OFFICIAL_LOGO,
        ChecklistItemCode.QR_CODE,
        ChecklistItemCode.REGISTRATION_LINK_AND_CONTACTS,
    ]:
        resp = api_client.post(
            f"/api/v1/creatives/requests/{req.id}/versions/{version.id}/checklist/{item_code}/verify/",
            data={"status": ChecklistItemStatus.VERIFIED, "remarks": "Pass"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

    # 2. Try approve as Placement Officer -> 403 Forbidden
    resp = api_client.post(
        f"/api/v1/creatives/requests/{req.id}/versions/{version.id}/approve/",
        data={"comments": "Officer trying to approve"},
        format="json",
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    # 3. Approve as Placement Head -> 200 OK
    api_client.force_authenticate(user=placement_head_user)
    resp = api_client.post(
        f"/api/v1/creatives/requests/{req.id}/versions/{version.id}/approve/",
        data={"comments": "Placement Head approved for broadcast"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["is_approved"] is True
    assert resp.data["status"] == AssetVersionStatus.APPROVED


@pytest.mark.django_db
def test_21_api_auditor_read_only_access(api_client, approved_job, placement_officer_user, auditor_user):
    """API Security: Auditor has read-only access and cannot mutate requests."""
    req = create_creative_request(approved_job, placement_officer_user, "Auditor Inspection Request")
    api_client.force_authenticate(user=auditor_user)

    # GET is permitted
    get_resp = api_client.get(f"/api/v1/creatives/requests/{req.id}/")
    assert get_resp.status_code == status.HTTP_200_OK

    # POST create is denied
    post_resp = api_client.post(
        "/api/v1/creatives/requests/",
        data={"job_requirement_id": str(approved_job.id), "title": "Auditor Attempt"},
        format="json",
    )
    assert post_resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_22_api_student_denied_access(api_client, student_user):
    """API Security: Student role is strictly denied access to Creative Studio."""
    api_client.force_authenticate(user=student_user)
    response = api_client.get("/api/v1/creatives/requests/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_23_api_unauthenticated_request_denied(api_client):
    """API Security: Unauthenticated requests return 401."""
    response = api_client.get("/api/v1/creatives/requests/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_24_api_designer_queue_and_metrics(api_client, approved_job, placement_officer_user, designer_user):
    """API: Designer work queue and operational metrics."""
    create_creative_request(approved_job, placement_officer_user, "Assigned Task", assigned_designer=designer_user)

    api_client.force_authenticate(user=designer_user)
    queue_resp = api_client.get("/api/v1/creatives/requests/designer-queue/")
    assert queue_resp.status_code == status.HTTP_200_OK
    assert queue_resp.data["meta"]["count"] == 1

    metrics_resp = api_client.get("/api/v1/creatives/requests/metrics/")
    assert metrics_resp.status_code == status.HTTP_200_OK
    assert "total_active" in metrics_resp.data


@pytest.mark.django_db
def test_25_audit_log_recorded_for_creative_actions(approved_job, placement_officer_user, designer_user, valid_png_file):
    """Compliance: Audit logs are recorded for creative creation, version upload, and verification."""
    req = create_creative_request(approved_job, placement_officer_user, "Audit Test Request", assigned_designer=designer_user)
    assert AuditLog.objects.filter(action="CREATIVE_REQUEST_CREATED", resource_id=str(req.id)).exists()

    version = upload_asset_version(req, valid_png_file, designer_user)
    assert AuditLog.objects.filter(action="CREATIVE_VERSION_UPLOADED", resource_id=str(req.id)).exists()

    verify_checklist_item(version, ChecklistItemCode.FLYER_ACCURACY, ChecklistItemStatus.VERIFIED, placement_officer_user)
    assert AuditLog.objects.filter(action="CREATIVE_CHECKLIST_VERIFIED", resource_id=str(req.id)).exists()
