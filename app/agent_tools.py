from typing import Any

from app.filesystem_tools import list_directory, read_file
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

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )
