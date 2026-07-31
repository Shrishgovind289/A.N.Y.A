import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv("/opt/anya/.env")


def parse_paths(variable_name: str, default: str) -> list[Path]:
    raw_value = os.getenv(variable_name, default)

    return [
        Path(item.strip()).expanduser().resolve()
        for item in raw_value.split(",")
        if item.strip()
    ]


ALLOWED_PATHS = parse_paths(
    "ANYA_ALLOWED_PATHS",
    "/",
)

DENIED_PATHS = parse_paths(
    "ANYA_DENIED_PATHS",
    "/home/sg_inspiron_server/Documents",
)


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def resolve_allowed_path(path_string: str) -> Path:
    requested_path = Path(path_string).expanduser().resolve()

    if not any(
        is_within(requested_path, allowed)
        for allowed in ALLOWED_PATHS
    ):
        raise PermissionError(
            f"Path is outside ANYA's allowed locations: {requested_path}"
        )

    if any(
        is_within(requested_path, denied)
        for denied in DENIED_PATHS
    ):
        raise PermissionError(
            f"Access is blocked for this path: {requested_path}"
        )

    return requested_path


def list_directory(
    path_string: str,
    max_entries: int = 200,
) -> dict:
    directory = resolve_allowed_path(path_string)

    if not directory.exists():
        raise FileNotFoundError(
            f"Directory does not exist: {directory}"
        )

    if not directory.is_dir():
        raise NotADirectoryError(
            f"Path is not a directory: {directory}"
        )

    max_entries = max(
        1,
        min(max_entries, 200),
    )

    entries = []

    for item in sorted(
        directory.iterdir(),
        key=lambda entry: (
            not entry.is_dir(),
            entry.name.lower(),
        ),
    ):
        try:
            resolve_allowed_path(str(item))
        except PermissionError:
            continue

        try:
            item_type = (
                "directory"
                if item.is_dir()
                else "file"
                if item.is_file()
                else "other"
            )

            entries.append(
                {
                    "name": item.name,
                    "type": item_type,
                    "size_bytes": (
                        item.stat().st_size
                        if item.is_file()
                        else None
                    ),
                }
            )

        except PermissionError:
            entries.append(
                {
                    "name": item.name,
                    "type": "permission_denied",
                    "size_bytes": None,
                }
            )

        if len(entries) >= max_entries:
            break

    directory_names = [
        entry["name"]
        for entry in entries
        if entry["type"] == "directory"
    ]

    file_names = [
        entry["name"]
        for entry in entries
        if entry["type"] == "file"
    ]

    authoritative_lines = [
        f"Visible entries in {directory}: {len(entries)} total.",
        "Directories: "
        + (
            ", ".join(directory_names)
            if directory_names
            else "none"
        ),
        "Files: "
        + (
            ", ".join(file_names)
            if file_names
            else "none"
        ),
    ]

    listing_complete = len(entries) < max_entries

    return {
        "path": str(directory),
        "authoritative_listing": "\n".join(authoritative_lines),
        "listing_complete": listing_complete,
        "instruction": (
            "Repeat every visible entry exactly. "
            "Do not omit entries or change the count. "
            "When listing_complete is true, state that the listing "
            "is complete and never claim additional entries exist. "
            "When listing_complete is false, state that the result "
            "may be truncated."
        ),
    }


def read_file(path_string: str) -> dict:
    file_path = resolve_allowed_path(path_string)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File does not exist: {file_path}"
        )

    if not file_path.is_file():
        raise IsADirectoryError(
            f"Path is not a regular file: {file_path}"
        )

    max_file_bytes = int(
        os.getenv("ANYA_MAX_FILE_BYTES", "262144")
    )

    file_size = file_path.stat().st_size

    if file_size > max_file_bytes:
        raise ValueError(
            f"File is too large to read: {file_size} bytes. "
            f"Maximum allowed size is {max_file_bytes} bytes."
        )

    content_bytes = file_path.read_bytes()

    if b"\x00" in content_bytes:
        raise ValueError(
            "Binary files cannot be read as text."
        )

    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "File is not valid UTF-8 text."
        ) from exc

    return {
        "path": str(file_path),
        "size_bytes": file_size,
        "content": content,
        "instruction": (
            "Use the file content exactly as provided. "
            "Do not invent missing content."
        ),
    }
