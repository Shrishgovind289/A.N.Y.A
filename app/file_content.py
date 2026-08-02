from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from pypdf import PdfReader


MAX_FILE_CONTENT_CHARS = int(
    os.getenv(
        "ANYA_MAX_FILE_CONTENT_CHARS",
        "12000",
    )
)

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".xml",
    ".py",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".js",
    ".html",
    ".css",
}


class FileContentError(Exception):
    pass


def truncate_content(
    content: str,
    character_limit: int,
) -> str:
    clean_content = content.strip()

    if len(clean_content) <= character_limit:
        return clean_content

    return (
        clean_content[:character_limit].rstrip()
        + "\n\n[File content truncated]"
    )


def extract_pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise FileContentError(
            f"Could not open PDF: {exc}"
        ) from exc

    pages: list[str] = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        try:
            page_text = page.extract_text() or ""
        except Exception as exc:
            page_text = (
                f"[Could not extract page "
                f"{page_number}: {exc}]"
            )

        page_text = page_text.strip()

        if page_text:
            pages.append(
                f"--- Page {page_number} ---\n"
                f"{page_text}"
            )

    if not pages:
        raise FileContentError(
            "The PDF contains no extractable text. "
            "It may be an image-only scanned document."
        )

    return "\n\n".join(pages)


def extract_text_file(path: Path) -> str:
    try:
        raw_content = path.read_bytes()
    except OSError as exc:
        raise FileContentError(
            f"Could not read file: {exc}"
        ) from exc

    if b"\x00" in raw_content:
        raise FileContentError(
            "The file appears to contain binary data."
        )

    return raw_content.decode(
        "utf-8",
        errors="replace",
    )


def encode_image_file(
    record: dict[str, Any],
) -> str:
    path = Path(record["storage_path"]).resolve()

    if not path.is_file():
        raise FileContentError(
            "The stored image could not be found."
        )

    extension = (
        record.get("extension")
        or path.suffix
    ).lower()

    if extension not in IMAGE_EXTENSIONS:
        raise FileContentError(
            "The attachment is not a supported image."
        )

    try:
        image_bytes = path.read_bytes()
    except OSError as exc:
        raise FileContentError(
            f"Could not read image: {exc}"
        ) from exc

    if not image_bytes:
        raise FileContentError(
            "The image file is empty."
        )

    return base64.b64encode(
        image_bytes
    ).decode("ascii")


def extract_file_content(
    record: dict[str, Any],
) -> str:
    path = Path(record["storage_path"]).resolve()

    if not path.is_file():
        raise FileContentError(
            "The stored file could not be found."
        )

    extension = (
        record.get("extension")
        or path.suffix
    ).lower()

    if extension == ".pdf":
        content = extract_pdf_text(path)
    elif extension in TEXT_EXTENSIONS:
        content = extract_text_file(path)
    else:
        raise FileContentError(
            f"Reading {extension or 'this file type'} "
            "inside chat is not supported yet."
        )

    return truncate_content(
        content,
        MAX_FILE_CONTENT_CHARS,
    )
