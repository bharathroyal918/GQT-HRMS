"""File validation and path generation utilities for Student Resumes."""
import hashlib
import os
import uuid
from django.core.exceptions import ValidationError
from django.utils.text import get_valid_filename

MAX_RESUME_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_resume_pdf(file_obj) -> str:
    """Validate that the uploaded file is a valid PDF and does not exceed size limits.

    Performs:
    1. Size boundary enforcement (<= 5MB).
    2. Cryptographic binary signature inspection (must start with b'%PDF-').
    3. Computation of SHA-256 hash.

    Returns:
        Hex-encoded SHA-256 digest string.
    Raises:
        ValidationError if size or signature checks fail.
    """
    if file_obj.size > MAX_RESUME_UPLOAD_SIZE_BYTES:
        raise ValidationError(
            f"File size of {file_obj.size} bytes exceeds the maximum allowable limit of "
            f"{MAX_RESUME_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # Inspect magic bytes
    file_obj.seek(0)
    magic_header = file_obj.read(5)
    file_obj.seek(0)

    if magic_header != b"%PDF-":
        raise ValidationError(
            "Security verification failed: File is not a valid PDF document. "
            "Binary magic bytes signature mismatch (expected '%PDF-')."
        )

    # Compute SHA-256 hash
    hasher = hashlib.sha256()
    for chunk in file_obj.chunks(chunk_size=65536):
        hasher.update(chunk)
    file_obj.seek(0)

    return hasher.hexdigest()


def student_resume_upload_path(instance, filename: str) -> str:
    """Generate safe, isolated storage path for student resumes.

    Format: student_resumes/user_<user_id>/resume_v<version_number>_<random_id>.pdf
    """
    ext = os.path.splitext(filename)[1].lower() or ".pdf"
    clean_name = f"resume_v{instance.version_number}_{uuid.uuid4().hex[:10]}{ext}"
    user_id = instance.student.user_id if hasattr(instance, "student") else "general"
    return f"student_resumes/user_{user_id}/{clean_name}"
