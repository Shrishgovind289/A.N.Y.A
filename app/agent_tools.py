from typing import Any

from app.filesystem_tools import list_directory, read_file
from app.github_tools import (
    list_github_branches,
    list_github_commits,
    list_github_directory,
    list_github_issues,
    list_github_pull_requests,
    list_github_repositories,
    read_github_file,
)
from app.internet_tools import fetch_webpage, web_search
from app.tools import get_gpu_status, get_server_status, get_system_health_report


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_server_status",
            "description": (
                "Get the current read-only status of the home server, "
                "including uptime, CPU, memory, and root disk usage."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_gpu_status",
            "description": (
                "Get the current read-only NVIDIA GPU status, "
                "including model, driver, temperature, utilization, "
                "and video memory usage."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_health_report",
            "description": (
                "Get an authoritative combined health report for the "
                "server and NVIDIA GPU. Prefer this tool when the user "
                "asks for an overall system or hardware health report."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": (
                "List files and folders inside an allowed directory. "
                "This tool is read-only. Blocked and sensitive paths "
                "are hidden automatically."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path_string": {
                        "type": "string",
                        "description": (
                            "Absolute directory path to list."
                        ),
                    },
                    "max_entries": {
                        "type": "integer",
                        "description": (
                            "Maximum number of entries to return, "
                            "between 1 and 200."
                        ),
                        "minimum": 1,
                        "maximum": 200,
                        "default": 50,
                    },
                },
                "required": ["path_string"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the contents of an allowed UTF-8 text file. "
                "The tool is read-only and blocks sensitive, binary, "
                "and oversized files."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path_string": {
                        "type": "string",
                        "description": (
                            "Absolute path of the text file to read."
                        ),
                    },
                },
                "required": ["path_string"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the public internet for current information. "
                "Returns result titles, URLs, and short summaries. "
                "Search results are not full webpage contents."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": (
                            "Maximum results to return, between 1 and 10."
                        ),
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": (
                "Open a public HTTP or HTTPS webpage and extract its "
                "readable text. Local and private network addresses, "
                "credentials, unsupported files, and oversized pages "
                "are blocked."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The complete public HTTP or HTTPS URL."
                        ),
                    },
                },
                "required": ["url"],
            },
        },
    },


    {
        "type": "function",
        "function": {
            "name": "list_github_repositories",
            "description": (
                "List GitHub repositories accessible through A.N.Y.A's "
                "configured read-only GitHub token."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_github_branches",
            "description": (
                "List branches in an accessible GitHub repository."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in owner/name format.",
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 30,
                    },
                },
                "required": ["repository"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_github_directory",
            "description": (
                "List files and directories at a path in an accessible "
                "GitHub repository."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in owner/name format.",
                    },
                    "path": {
                        "type": "string",
                        "description": (
                            "Repository-relative directory path. "
                            "Use an empty string for the root."
                        ),
                        "default": "",
                    },
                    "ref": {
                        "type": "string",
                        "description": (
                            "Optional branch, tag, or commit SHA."
                        ),
                        "default": "",
                    },
                },
                "required": ["repository"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_github_file",
            "description": (
                "Read a UTF-8 text file from an accessible GitHub "
                "repository. This tool is read-only."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in owner/name format.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Repository-relative file path.",
                    },
                    "ref": {
                        "type": "string",
                        "description": (
                            "Optional branch, tag, or commit SHA."
                        ),
                        "default": "",
                    },
                },
                "required": [
                    "repository",
                    "path",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_github_commits",
            "description": (
                "List recent commits from an accessible GitHub repository."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in owner/name format.",
                    },
                    "ref": {
                        "type": "string",
                        "description": (
                            "Optional branch, tag, or commit SHA."
                        ),
                        "default": "",
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10,
                    },
                },
                "required": ["repository"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_github_issues",
            "description": (
                "List issues from an accessible GitHub repository."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in owner/name format.",
                    },
                    "state": {
                        "type": "string",
                        "enum": [
                            "open",
                            "closed",
                            "all",
                        ],
                        "default": "open",
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 20,
                    },
                },
                "required": ["repository"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_github_pull_requests",
            "description": (
                "List pull requests from an accessible GitHub repository."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in owner/name format.",
                    },
                    "state": {
                        "type": "string",
                        "enum": [
                            "open",
                            "closed",
                            "all",
                        ],
                        "default": "open",
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 20,
                    },
                },
                "required": ["repository"],
            },
        },
    },

]


def execute_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    arguments = arguments or {}

    if tool_name == "get_server_status":
        if arguments:
            raise ValueError(
                "get_server_status does not accept arguments"
            )

        return get_server_status()

    if tool_name == "get_gpu_status":
        if arguments:
            raise ValueError(
                "get_gpu_status does not accept arguments"
            )

        return get_gpu_status()

    if tool_name == "get_system_health_report":
        if arguments:
            raise ValueError(
                "get_system_health_report does not accept arguments"
            )

        return get_system_health_report()

    if tool_name == "list_directory":
        return list_directory(
            path_string=arguments.get("path_string", ""),
            max_entries=arguments.get("max_entries", 50),
        )

    if tool_name == "read_file":
        return read_file(
            path_string=arguments.get("path_string", ""),
        )

    if tool_name == "web_search":
        return web_search(
            query=arguments.get("query", ""),
            max_results=arguments.get("max_results", 5),
        )

    if tool_name == "fetch_webpage":
        return fetch_webpage(
            url=arguments.get("url", ""),
        )

    if tool_name == "list_github_repositories":
        return list_github_repositories(
            max_results=arguments.get(
                "max_results",
                20,
            ),
        )

    if tool_name == "list_github_branches":
        return list_github_branches(
            repository=arguments.get(
                "repository",
                "",
            ),
            max_results=arguments.get(
                "max_results",
                30,
            ),
        )

    if tool_name == "list_github_directory":
        return list_github_directory(
            repository=arguments.get(
                "repository",
                "",
            ),
            path=arguments.get(
                "path",
                "",
            ),
            ref=arguments.get(
                "ref",
                "",
            ),
        )

    if tool_name == "read_github_file":
        return read_github_file(
            repository=arguments.get(
                "repository",
                "",
            ),
            path=arguments.get(
                "path",
                "",
            ),
            ref=arguments.get(
                "ref",
                "",
            ),
        )

    if tool_name == "list_github_commits":
        return list_github_commits(
            repository=arguments.get(
                "repository",
                "",
            ),
            ref=arguments.get(
                "ref",
                "",
            ),
            max_results=arguments.get(
                "max_results",
                10,
            ),
        )

    if tool_name == "list_github_issues":
        return list_github_issues(
            repository=arguments.get(
                "repository",
                "",
            ),
            state=arguments.get(
                "state",
                "open",
            ),
            max_results=arguments.get(
                "max_results",
                20,
            ),
        )

    if tool_name == "list_github_pull_requests":
        return list_github_pull_requests(
            repository=arguments.get(
                "repository",
                "",
            ),
            state=arguments.get(
                "state",
                "open",
            ),
            max_results=arguments.get(
                "max_results",
                20,
            ),
        )

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )
