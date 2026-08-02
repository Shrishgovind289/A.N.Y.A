import base64
import os
import re
from urllib.parse import quote

import httpx


GITHUB_API_URL = os.getenv(
    "GITHUB_API_URL",
    "https://api.github.com",
).rstrip("/")

GITHUB_API_VERSION = os.getenv(
    "GITHUB_API_VERSION",
    "2026-03-10",
)

GITHUB_TIMEOUT_SECONDS = float(
    os.getenv(
        "ANYA_GITHUB_TIMEOUT_SECONDS",
        "20",
    )
)

GITHUB_MAX_FILE_BYTES = int(
    os.getenv(
        "ANYA_GITHUB_MAX_FILE_BYTES",
        "500000",
    )
)

_REPOSITORY_PATTERN = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
)


class GitHubToolError(RuntimeError):
    pass


def _require_token() -> str:
    token = os.getenv(
        "GITHUB_TOKEN",
        "",
    ).strip()

    if not token:
        raise GitHubToolError(
            "GitHub access is not configured."
        )

    return token


def _validate_repository(
    repository: str,
) -> str:
    repository = repository.strip()

    if not _REPOSITORY_PATTERN.fullmatch(
        repository
    ):
        raise GitHubToolError(
            "Repository must use owner/name format."
        )

    return repository


def _github_get(
    endpoint: str,
    params: dict | None = None,
):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": (
            f"Bearer {_require_token()}"
        ),
        "X-GitHub-Api-Version": (
            GITHUB_API_VERSION
        ),
        "User-Agent": "ANYA-Home-Server",
    }

    try:
        response = httpx.get(
            f"{GITHUB_API_URL}{endpoint}",
            headers=headers,
            params=params,
            timeout=GITHUB_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
    except httpx.TimeoutException as exc:
        raise GitHubToolError(
            "GitHub request timed out."
        ) from exc
    except httpx.HTTPError as exc:
        raise GitHubToolError(
            "GitHub could not be reached."
        ) from exc

    if response.status_code == 401:
        raise GitHubToolError(
            "GitHub rejected the configured token."
        )

    if response.status_code == 403:
        raise GitHubToolError(
            "GitHub denied access or the rate limit was reached."
        )

    if response.status_code == 404:
        raise GitHubToolError(
            "Repository or GitHub resource was not found."
        )

    if not response.is_success:
        raise GitHubToolError(
            f"GitHub returned HTTP {response.status_code}."
        )

    try:
        return response.json()
    except ValueError as exc:
        raise GitHubToolError(
            "GitHub returned an invalid response."
        ) from exc


def list_github_repositories(
    max_results: int = 20,
) -> dict:
    max_results = max(
        1,
        min(int(max_results), 100),
    )

    records = _github_get(
        "/user/repos",
        {
            "affiliation": (
                "owner,collaborator,"
                "organization_member"
            ),
            "sort": "updated",
            "direction": "desc",
            "per_page": max_results,
        },
    )

    repositories = []

    for record in records:
        repositories.append(
            {
                "name": record.get(
                    "full_name"
                ),
                "private": record.get(
                    "private"
                ),
                "description": record.get(
                    "description"
                ),
                "default_branch": record.get(
                    "default_branch"
                ),
                "language": record.get(
                    "language"
                ),
                "updated_at": record.get(
                    "updated_at"
                ),
                "url": record.get(
                    "html_url"
                ),
            }
        )

    return {
        "count": len(repositories),
        "repositories": repositories,
    }


def list_github_branches(
    repository: str,
    max_results: int = 30,
) -> dict:
    repository = _validate_repository(
        repository
    )

    max_results = max(
        1,
        min(int(max_results), 100),
    )

    records = _github_get(
        f"/repos/{repository}/branches",
        {
            "per_page": max_results,
        },
    )

    return {
        "repository": repository,
        "branches": [
            {
                "name": record.get("name"),
                "protected": record.get(
                    "protected"
                ),
                "commit_sha": (
                    record.get("commit") or {}
                ).get("sha"),
            }
            for record in records
        ],
    }


def list_github_directory(
    repository: str,
    path: str = "",
    ref: str = "",
) -> dict:
    repository = _validate_repository(
        repository
    )

    normalized_path = path.strip().strip("/")
    encoded_path = quote(
        normalized_path,
        safe="/",
    )

    endpoint = (
        f"/repos/{repository}/contents"
    )

    if encoded_path:
        endpoint += f"/{encoded_path}"

    params = {}

    if ref.strip():
        params["ref"] = ref.strip()

    records = _github_get(
        endpoint,
        params or None,
    )

    if isinstance(records, dict):
        records = [records]

    entries = []

    for record in records:
        entries.append(
            {
                "name": record.get("name"),
                "path": record.get("path"),
                "type": record.get("type"),
                "size": record.get("size"),
                "sha": record.get("sha"),
                "url": record.get(
                    "html_url"
                ),
            }
        )

    return {
        "repository": repository,
        "path": normalized_path,
        "ref": ref.strip() or None,
        "entries": entries,
    }


def read_github_file(
    repository: str,
    path: str,
    ref: str = "",
) -> dict:
    repository = _validate_repository(
        repository
    )

    normalized_path = path.strip().strip("/")

    if not normalized_path:
        raise GitHubToolError(
            "A repository file path is required."
        )

    encoded_path = quote(
        normalized_path,
        safe="/",
    )

    params = {}

    if ref.strip():
        params["ref"] = ref.strip()

    record = _github_get(
        (
            f"/repos/{repository}/contents/"
            f"{encoded_path}"
        ),
        params or None,
    )

    if record.get("type") != "file":
        raise GitHubToolError(
            "The requested GitHub path is not a file."
        )

    size = int(record.get("size") or 0)

    if size > GITHUB_MAX_FILE_BYTES:
        raise GitHubToolError(
            "The GitHub file exceeds the configured read limit."
        )

    encoded_content = record.get(
        "content",
        "",
    ).replace("\n", "")

    if record.get("encoding") != "base64":
        raise GitHubToolError(
            "The GitHub file encoding is unsupported."
        )

    try:
        raw_content = base64.b64decode(
            encoded_content,
            validate=True,
        )
        text_content = raw_content.decode(
            "utf-8"
        )
    except (
        ValueError,
        UnicodeDecodeError,
    ) as exc:
        raise GitHubToolError(
            "The GitHub file is not readable UTF-8 text."
        ) from exc

    return {
        "repository": repository,
        "path": normalized_path,
        "ref": ref.strip() or None,
        "sha": record.get("sha"),
        "size": size,
        "url": record.get("html_url"),
        "content": text_content,
    }


def list_github_commits(
    repository: str,
    ref: str = "",
    max_results: int = 10,
) -> dict:
    repository = _validate_repository(
        repository
    )

    max_results = max(
        1,
        min(int(max_results), 50),
    )

    params = {
        "per_page": max_results,
    }

    if ref.strip():
        params["sha"] = ref.strip()

    records = _github_get(
        f"/repos/{repository}/commits",
        params,
    )

    commits = []

    for record in records:
        commit = record.get("commit") or {}
        author = commit.get("author") or {}

        commits.append(
            {
                "sha": record.get("sha"),
                "message": commit.get(
                    "message"
                ),
                "author": author.get(
                    "name"
                ),
                "date": author.get("date"),
                "url": record.get(
                    "html_url"
                ),
            }
        )

    return {
        "repository": repository,
        "ref": ref.strip() or None,
        "commits": commits,
    }


def list_github_issues(
    repository: str,
    state: str = "open",
    max_results: int = 20,
) -> dict:
    repository = _validate_repository(
        repository
    )

    if state not in {
        "open",
        "closed",
        "all",
    }:
        raise GitHubToolError(
            "Issue state must be open, closed, or all."
        )

    max_results = max(
        1,
        min(int(max_results), 50),
    )

    records = _github_get(
        f"/repos/{repository}/issues",
        {
            "state": state,
            "sort": "updated",
            "direction": "desc",
            "per_page": max_results,
        },
    )

    issues = []

    for record in records:
        if "pull_request" in record:
            continue

        issues.append(
            {
                "number": record.get(
                    "number"
                ),
                "title": record.get(
                    "title"
                ),
                "state": record.get(
                    "state"
                ),
                "author": (
                    record.get("user") or {}
                ).get("login"),
                "updated_at": record.get(
                    "updated_at"
                ),
                "url": record.get(
                    "html_url"
                ),
            }
        )

    return {
        "repository": repository,
        "state": state,
        "issues": issues,
    }


def list_github_pull_requests(
    repository: str,
    state: str = "open",
    max_results: int = 20,
) -> dict:
    repository = _validate_repository(
        repository
    )

    if state not in {
        "open",
        "closed",
        "all",
    }:
        raise GitHubToolError(
            "Pull-request state must be open, closed, or all."
        )

    max_results = max(
        1,
        min(int(max_results), 50),
    )

    records = _github_get(
        f"/repos/{repository}/pulls",
        {
            "state": state,
            "sort": "updated",
            "direction": "desc",
            "per_page": max_results,
        },
    )

    pull_requests = []

    for record in records:
        pull_requests.append(
            {
                "number": record.get(
                    "number"
                ),
                "title": record.get(
                    "title"
                ),
                "state": record.get(
                    "state"
                ),
                "draft": record.get(
                    "draft"
                ),
                "author": (
                    record.get("user") or {}
                ).get("login"),
                "head": (
                    record.get("head") or {}
                ).get("ref"),
                "base": (
                    record.get("base") or {}
                ).get("ref"),
                "updated_at": record.get(
                    "updated_at"
                ),
                "url": record.get(
                    "html_url"
                ),
            }
        )

    return {
        "repository": repository,
        "state": state,
        "pull_requests": pull_requests,
    }
