import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("ANYA_DATA_DIR", BASE_DIR / "data"))
PROJECTS_DIR = Path(os.getenv("ANYA_PROJECTS_DIR", BASE_DIR / "projects"))
DATABASE_PATH = DATA_DIR / "anya.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                workspace_path TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('system', 'user', 'assistant', 'tool')
                ),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id)
                    REFERENCES chats(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS project_files (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                extension TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                scan_status TEXT NOT NULL,
                scan_details TEXT NOT NULL DEFAULT '',
                storage_path TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_project_files_project_id
                ON project_files(project_id);


            CREATE INDEX IF NOT EXISTS idx_chats_project_id
                ON chats(project_id);

            CREATE INDEX IF NOT EXISTS idx_messages_chat_id
                ON messages(chat_id);
            """
        )


def make_project_folder_name(name: str, project_id: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-").lower()

    if not safe_name:
        safe_name = "project"

    return f"{safe_name}-{project_id[:8]}"


def create_project(name: str, description: str = "") -> dict[str, Any]:
    clean_name = name.strip()

    if not clean_name:
        raise ValueError("Project name cannot be empty.")

    project_id = str(uuid.uuid4())
    timestamp = utc_now()

    folder_name = make_project_folder_name(clean_name, project_id)
    workspace_path = PROJECTS_DIR / folder_name
    workspace_path.mkdir(parents=True, exist_ok=False)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO projects (
                id,
                name,
                description,
                workspace_path,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                clean_name,
                description.strip(),
                str(workspace_path),
                timestamp,
                timestamp,
            ),
        )

    return get_project(project_id)


def get_project(project_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                description,
                workspace_path,
                created_at,
                updated_at
            FROM projects
            WHERE id = ?
            """,
            (project_id,),
        ).fetchone()

    return dict(row) if row else None


def list_projects() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                name,
                description,
                workspace_path,
                created_at,
                updated_at
            FROM projects
            ORDER BY updated_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def create_chat(
    title: str = "New Chat",
    project_id: str | None = None,
) -> dict[str, Any]:
    if project_id is not None and get_project(project_id) is None:
        raise ValueError("Project does not exist.")

    chat_id = str(uuid.uuid4())
    timestamp = utc_now()
    clean_title = title.strip() or "New Chat"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO chats (
                id,
                project_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                project_id,
                clean_title,
                timestamp,
                timestamp,
            ),
        )

    return get_chat(chat_id)


def get_chat(chat_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                project_id,
                title,
                created_at,
                updated_at
            FROM chats
            WHERE id = ?
            """,
            (chat_id,),
        ).fetchone()

    return dict(row) if row else None


def list_chats(project_id: str | None = None) -> list[dict[str, Any]]:
    with get_connection() as connection:
        if project_id is None:
            rows = connection.execute(
                """
                SELECT
                    id,
                    project_id,
                    title,
                    created_at,
                    updated_at
                FROM chats
                ORDER BY updated_at DESC
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT
                    id,
                    project_id,
                    title,
                    created_at,
                    updated_at
                FROM chats
                WHERE project_id = ?
                ORDER BY updated_at DESC
                """,
                (project_id,),
            ).fetchall()

    return [dict(row) for row in rows]


def add_message(chat_id: str, role: str, content: str) -> dict[str, Any]:
    if get_chat(chat_id) is None:
        raise ValueError("Chat does not exist.")

    if role not in {"system", "user", "assistant", "tool"}:
        raise ValueError("Invalid message role.")

    timestamp = utc_now()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO messages (
                chat_id,
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                chat_id,
                role,
                content,
                timestamp,
            ),
        )

        connection.execute(
            """
            UPDATE chats
            SET updated_at = ?
            WHERE id = ?
            """,
            (
                timestamp,
                chat_id,
            ),
        )

        row = connection.execute(
            """
            SELECT
                id,
                chat_id,
                role,
                content,
                created_at
            FROM messages
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    return dict(row)


def get_chat_messages(chat_id: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                chat_id,
                role,
                content,
                created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def create_file_record(
    metadata: dict[str, Any],
) -> dict[str, Any]:
    timestamp = utc_now()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO project_files (
                id,
                project_id,
                original_name,
                stored_name,
                extension,
                content_type,
                size_bytes,
                sha256,
                scan_status,
                scan_details,
                storage_path,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metadata["id"],
                metadata["project_id"],
                metadata["original_name"],
                metadata["stored_name"],
                metadata["extension"],
                metadata["content_type"],
                metadata["size_bytes"],
                metadata["sha256"],
                metadata["scan_status"],
                metadata.get("scan_details", ""),
                metadata["storage_path"],
                timestamp,
            ),
        )

    return get_file_record(metadata["id"])


def get_file_record(
    file_id: str,
) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                project_id,
                original_name,
                stored_name,
                extension,
                content_type,
                size_bytes,
                sha256,
                scan_status,
                scan_details,
                storage_path,
                created_at
            FROM project_files
            WHERE id = ?
            """,
            (file_id,),
        ).fetchone()

    return dict(row) if row else None


def list_project_files(
    project_id: str,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                project_id,
                original_name,
                stored_name,
                extension,
                content_type,
                size_bytes,
                sha256,
                scan_status,
                scan_details,
                storage_path,
                created_at
            FROM project_files
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def delete_file_record(
    file_id: str,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM project_files
            WHERE id = ?
            """,
            (file_id,),
        )
