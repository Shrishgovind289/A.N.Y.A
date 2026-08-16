SERVER_TOOL_NAMES = {
    "get_server_status",
    "get_gpu_status",
    "get_system_health_report",
}

SERVER_CONTEXT_TERMS = (
    "server",
    "system health",
    "health report",
    "cpu",
    "processor",
    "gpu",
    "nvidia",
    "vram",
    "memory",
    "ram",
    "disk",
    "storage",
    "uptime",
    "temperature",
    "thermal",
    "utilization",
    "hardware",
    "ollama",
)


def build_recent_context(
    message: str,
    history: list[dict],
    max_items: int = 8,
) -> str:
    parts = []

    for item in history[-max_items:]:
        content = str(
            item.get("content", "")
        ).strip()

        if content:
            parts.append(content)

    parts.append(message)

    return " ".join(parts).lower()


def is_tool_call_relevant(
    tool_name: str,
    message: str,
    history: list[dict],
) -> bool:
    if tool_name not in SERVER_TOOL_NAMES:
        return True

    context = build_recent_context(
        message,
        history,
    )

    return any(
        term in context
        for term in SERVER_CONTEXT_TERMS
    )
