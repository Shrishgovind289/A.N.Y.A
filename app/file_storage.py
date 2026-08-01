import hashlib
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

from app.database import get_project


MAX_UPLOAD_BYTES = int(
    os.getenv(
        "ANYA_MAX_UPLOAD_BYTES",
        str(50 * 1024 * 1024),
    )
)

SCAN_TIMEOUT_SECONDS = int(
    os.getenv(
        "ANYA_SCAN_TIMEOUT_SECONDS",
        "120",
    )
)

ALLOWED_EXTENSIONS = {
    extension.strip().lower()
    for extension in os.getenv(
        "ANYA_ALLOWED_UPLOAD_EXTENSIONS",
        (
            ".txt,.md,.pdf,.csv,.json,.xml,"
            ".py,.c,.h,.cpp,.hpp,.js,.html,.css,"
            ".png,.jpg,.jpeg,.webp,.gif,"
            ".zip,.tar,.gz,.docx,.xlsx,.pptx"
        ),
    ).split(",")
    if extension.strip()
}


class UploadError(Exception):
    pass


class MalwareDetectedError(UploadError):
    pass


class ScannerUnavailableError(UploadError):
    pass


def sanitize_filename(filename: str) -> str:
    original_name = Path(filename or "").name.strip()

    if not original_name:
        raise UploadError("The uploaded file has no valid name.")

    safe_name = re.sub(
        r"[^A-Za-z0-9._ -]+",
        "_",
        original_name,
    )

    safe_name = re.sub(
        r"\s+",
        " ",
        safe_name,
    ).strip(" .")

    if not safe_name:
        raise UploadError("The uploaded filename is invalid.")

    if len(safe_name) > 180:
        suffix = Path(safe_name).suffix
        stem_limit = max(1, 180 - len(suffix))
        safe_name = safe_name[:stem_limit] + suffix

    return safe_name


def validate_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()

    if not extension:
        raise UploadError(
            "Files without an extension are not allowed."
        )

    if extension not in ALLOWED_EXTENSIONS:
        raise UploadError(
            f"Files with the '{extension}' extension are not allowed."
        )

    return extension


def calculate_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()

    with file_path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def scan_file(file_path: Path) -> dict[str, Any]:
    scanner = shutil.which("clamscan")

    if scanner is None:
        raise ScannerUnavailableError(
            "ClamAV scanner is not installed."
        )

    result = subprocess.run(
        [
            scanner,
            "--no-summary",
            "--infected",
            str(file_path),
        ],
        capture_output=True,
        text=True,
        timeout=SCAN_TIMEOUT_SECONDS,
        check=False,
    )

    output = "\n".join(
        part.strip()
        for part in (
            result.stdout,
            result.stderr,
        )
        if part.strip()
    )

    if result.returncode == 1:
        raise MalwareDetectedError(
            output or "Malware was detected."
        )

    if result.returncode != 0:
        raise UploadError(
            output
            or (
                "ClamAV could not complete "
                f"the scan. Exit code: {result.returncode}"
            )
        )

    return {
        "scanner": "ClamAV",
        "status": "clean",
        "details": output or "No threats detected.",
    }


def store_scanned_file(
    project_id: str,
    temporary_path: Path,
    original_filename: str,
    content_type: str | None,
) -> dict[str, Any]:
    project = get_project(project_id)

    if project is None:
        raise UploadError("Project does not exist.")

    safe_filename = sanitize_filename(
        original_filename
    )

    extension = validate_extension(
        safe_filename
    )

    file_size = temporary_path.stat().st_size

    if file_size <= 0:
        raise UploadError("The uploaded file is empty.")

    if file_size > MAX_UPLOAD_BYTES:
        raise UploadError(
            "The uploaded file exceeds the "
            f"{MAX_UPLOAD_BYTES}-byte limit."
        )

    sha256 = calculate_sha256(
        temporary_path
    )

    scan_result = scan_file(
        temporary_path
    )

    file_id = str(uuid.uuid4())

    workspace_path = Path(
        project["workspace_path"]
    ).resolve()

    upload_directory = (
        workspace_path
        / "uploads"
        / file_id
    )

    upload_directory.mkdir(
        parents=True,
        exist_ok=False,
    )

    destination_path = (
        upload_directory
        / safe_filename
    )

    shutil.move(
        str(temporary_path),
        destination_path,
    )

    return {
        "id": file_id,
        "project_id": project_id,
        "original_name": original_filename,
        "stored_name": safe_filename,
        "extension": extension,
        "content_type": (
            content_type
            or "application/octet-stream"
        ),
        "size_bytes": file_size,
        "sha256": sha256,
        "scan_status": scan_result["status"],
        "scan_details": scan_result["details"],
        "storage_path": str(destination_path),
    }
