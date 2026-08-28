import sqlite3
from pathlib import Path
from threading import Lock


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LEARNING_DB_PATH = DATA_DIR / "learning.db"

_db_lock = Lock()


def learning_store_init() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with _db_lock:
        with sqlite3.connect(LEARNING_DB_PATH) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    prompt TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    model_used TEXT NOT NULL,

                    answer TEXT,

                    is_correct INTEGER,

                    mistake TEXT,
                    corrected_answer TEXT,
                    lesson TEXT,

                    verification_method TEXT,

                    created_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_learning_task_type
                ON learning_records(task_type)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_learning_model
                ON learning_records(model_used)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_learning_correct
                ON learning_records(is_correct)
                """
            )

            connection.commit()


def learning_store_add(
    prompt: str,
    task_type: str,
    model_used: str,
    answer: str | None = None,
    is_correct: bool | None = None,
    mistake: str | None = None,
    corrected_answer: str | None = None,
    lesson: str | None = None,
    verification_method: str | None = None,
) -> int:
    with _db_lock:
        with sqlite3.connect(LEARNING_DB_PATH) as connection:
            cursor = connection.execute(
                """
                INSERT INTO learning_records (
                    prompt,
                    task_type,
                    model_used,
                    answer,
                    is_correct,
                    mistake,
                    corrected_answer,
                    lesson,
                    verification_method
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prompt,
                    task_type,
                    model_used,
                    answer,
                    None if is_correct is None else int(is_correct),
                    mistake,
                    corrected_answer,
                    lesson,
                    verification_method,
                ),
            )

            connection.commit()

            if cursor.lastrowid is None:
                raise RuntimeError(
                    "Failed to create learning record."
                )

            return cursor.lastrowid


def learning_store_get_lessons(
    task_type: str,
    limit: int = 5,
) -> list[dict]:
    with _db_lock:
        with sqlite3.connect(LEARNING_DB_PATH) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                """
                SELECT
                    id,
                    prompt,
                    model_used,
                    mistake,
                    corrected_answer,
                    lesson,
                    verification_method,
                    created_at
                FROM learning_records
                WHERE
                    task_type = ?
                    AND is_correct = 0
                    AND lesson IS NOT NULL
                    AND TRIM(lesson) != ''
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    task_type,
                    limit,
                ),
            ).fetchall()

    return [dict(row) for row in rows]

def learning_store_get_model_stats(
    task_type: str,
) -> list[dict]:
    with _db_lock:
        with sqlite3.connect(LEARNING_DB_PATH) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                """
                SELECT
                    model_used,
                    COUNT(*) AS total_feedback,
                    SUM(
                        CASE
                            WHEN is_correct = 1 THEN 1
                            ELSE 0
                        END
                    ) AS correct_count,
                    SUM(
                        CASE
                            WHEN is_correct = 0 THEN 1
                            ELSE 0
                        END
                    ) AS incorrect_count
                FROM learning_records
                WHERE
                    task_type = ?
                    AND is_correct IS NOT NULL
                GROUP BY model_used
                """,
                (task_type,),
            ).fetchall()

    results = []

    for row in rows:
        record = dict(row)

        total = record["total_feedback"]
        correct = record["correct_count"]

        record["success_rate"] = (
            correct / total
            if total > 0
            else 0.0
        )

        results.append(record)

    return results