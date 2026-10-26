"""File upload security, binary magic bytes validation, and asset metadata extraction."""
import hashlib
import os
import struct
import uuid
from typing import Dict, Any, Optional, Tuple
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

# Configurable limits
MAX_CREATIVE_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
PROHIBITED_EXTENSIONS = {
    ".svg", ".html", ".htm", ".xml", ".xhtml", ".js", ".mjs", ".exe",
    ".dll", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".jar", ".py", ".php"
}

ALLOWED_MIME_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}

# Signatures (Magic Bytes)
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_PDF = b"%PDF-"
MAGIC_RIFF = b"RIFF"
MAGIC_WEBP = b"WEBP"


def _extract_image_dimensions(header: bytes, ext: str) -> Tuple[Optional[int], Optional[int]]:
    """Extract width and height in pixels from raw file headers without third-party dependencies."""
    try:
        if ext == ".png" and len(header) >= 24:
            # IHDR chunk dimensions are at offset 16 to 24 (4 bytes width, 4 bytes height big-endian)
            width, height = struct.unpack(">II", header[16:24])
            return width, height

        elif ext in (".jpg", ".jpeg"):
            # JPEG: Scan markers for SOF0 (0xFFC0), SOF2 (0xFFC2)
            idx = 2
            length = len(header)
            while idx < length - 9:
                if header[idx] != 0xFF:
                    idx += 1
                    continue
                marker = header[idx + 1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    # Height at idx + 5, Width at idx + 7 (big endian 2 bytes each)
                    height, width = struct.unpack(">HH", header[idx + 5:idx + 9])
                    return width, height
                else:
                    # Skip segment length
                    if idx + 4 > length:
                        break
                    segment_len = struct.unpack(">H", header[idx + 2:idx + 4])[0]
                    idx += 2 + segment_len

        elif ext == ".webp" and len(header) >= 30:
            if header[12:16] == b"VP8 ":
                # Simple lossy VP8
                width, height = struct.unpack("<HH", header[26:30])
                return width & 0x3FFF, height & 0x3FFF
            elif header[12:16] == b"VP8X":
                # Extended VP8X: canvas width at 24:27 (24 bits), height at 27:30 (24 bits)
                width = 1 + struct.unpack("<I", header[24:27] + b"\x00")[0]
                height = 1 + struct.unpack("<I", header[27:30] + b"\x00")[0]
                return width, height
            elif header[12:16] == b"VP8L":
                # Lossless VP8L
                b0, b1, b2, b3 = header[21:25]
                width = 1 + (((b1 & 0x3F) << 8) | b0)
                height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
                return width, height

    except Exception:
        # Graceful fallback: return None if parsing non-standard file layout
        pass

    return None, None


def validate_and_sanitize_creative_file(uploaded_file: UploadedFile) -> Dict[str, Any]:
    """Inspect and validate an uploaded promotional asset file.
    
    Security enforcement:
    1. Size limit enforcement (<= 10MB).
    2. Strictly rejects active content (SVG, HTML, Scripts) to prevent Stored XSS.
    3. Filename normalization preventing path traversal.
    4. Exact binary magic bytes signature matching.
    5. Computes cryptographic SHA-256 digest.
    6. Extracts dimensions (width, height in pixels) where applicable.
    7. Generates random server-controlled storage filename.
    """
    if not uploaded_file:
        raise ValidationError("No file was provided for upload.")

    # 1. Size check
    file_size = uploaded_file.size
    if file_size <= 0:
        raise ValidationError("Uploaded file is empty (0 bytes).")
    if file_size > MAX_CREATIVE_UPLOAD_SIZE_BYTES:
        max_mb = MAX_CREATIVE_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise ValidationError(f"File size exceeds the maximum permitted limit of {max_mb} MB.")

    # 2. Filename and extension normalization
    original_name = os.path.basename(uploaded_file.name or "asset")
    _, raw_ext = os.path.splitext(original_name)
    ext = raw_ext.lower().strip()

    if ext in PROHIBITED_EXTENSIONS or ext == ".svg":
        raise ValidationError(
            f"File format '{ext}' is strictly prohibited for security reasons. "
            f"SVGs and executable or scriptable formats are not permitted. "
            f"Allowed formats: PNG, JPEG, WEBP, PDF."
        )

    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file extension '{ext}'. "
            f"Permitted formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # 3. Read header (first 4KB for signature inspection)
    uploaded_file.seek(0)
    header = uploaded_file.read(4096)

    # Reject active content / script tags embedded in file header
    lower_header = header[:1024].lower()
    if (
        b"<svg" in lower_header
        or b"<?xml" in lower_header
        or b"<html" in lower_header
        or b"<script" in lower_header
        or b"onload=" in lower_header
        or b"onerror=" in lower_header
    ):
        raise ValidationError("File content contains prohibited markup or script elements.")

    # 4. Binary Magic Bytes verification
    detected_mime: Optional[str] = None
    if header.startswith(MAGIC_PNG):
        detected_mime = "image/png"
    elif header.startswith(MAGIC_JPEG):
        detected_mime = "image/jpeg"
    elif header.startswith(MAGIC_RIFF) and len(header) >= 12 and header[8:12] == MAGIC_WEBP:
        detected_mime = "image/webp"
    elif header.startswith(MAGIC_PDF):
        detected_mime = "application/pdf"
    else:
        raise ValidationError(
            "File header signature does not match any allowed format (PNG, JPEG, WEBP, PDF). "
            "File content may be corrupted or disguised."
        )

    # Cross-reference extension with signature
    if ext == ".png" and detected_mime != "image/png":
        raise ValidationError("File extension is .png but binary signature is not a valid PNG image.")
    elif ext in (".jpg", ".jpeg") and detected_mime != "image/jpeg":
        raise ValidationError("File extension indicates JPEG but binary signature is not a valid JPEG.")
    elif ext == ".webp" and detected_mime != "image/webp":
        raise ValidationError("File extension indicates WEBP but binary signature is not a valid WEBP image.")
    elif ext == ".pdf" and detected_mime != "application/pdf":
        raise ValidationError("File extension indicates PDF but binary signature is not a valid PDF document.")

    # 5. Compute SHA-256 hash and extract dimensions
    uploaded_file.seek(0)
    hasher = hashlib.sha256()
    while chunk := uploaded_file.read(65536):
        hasher.update(chunk)
    sha256_digest = hasher.hexdigest()

    # Reset seek position for storage write
    uploaded_file.seek(0)

    width_px, height_px = _extract_image_dimensions(header, ext)

    # 6. Generate server-controlled non-guessable storage filename
    safe_storage_name = f"{uuid.uuid4().hex}{ext}"

    return {
        "original_filename": original_name,
        "storage_filename": safe_storage_name,
        "file_size_bytes": file_size,
        "mime_type": detected_mime,
        "sha256_hash": sha256_digest,
        "width_px": width_px,
        "height_px": height_px,
        "extension": ext,
    }
