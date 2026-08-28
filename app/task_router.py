from enum import StrEnum


class TaskType(StrEnum):
    GENERAL = "general"
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    IMAGE_ANALYSIS = "image_analysis"
    SERVER_ADMIN = "server_admin"
    GITHUB = "github"


def classify_task(
    prompt: str,
    has_images: bool = False,
) -> TaskType:
    text = prompt.lower()

    if has_images:
        return TaskType.IMAGE_ANALYSIS

    github_keywords = (
        "github",
        "repository",
        "repo",
        "pull request",
        "commit",
        "branch",
    )

    if any(keyword in text for keyword in github_keywords):
        return TaskType.GITHUB

    server_keywords = (
        "server status",
        "server health",
        "docker",
        "systemctl",
        "journalctl",
        "disk usage",
        "filesystem",
        "cpu usage",
        "memory usage",
    )

    if any(keyword in text for keyword in server_keywords):
        return TaskType.SERVER_ADMIN

    code_markers = (
        "#include",
        "int main(",
        "void ",
        "uint8_t",
        "uint16_t",
        "uint32_t",
        "printf(",
        "def ",
        "class ",
        "import ",
        "for (",
        "while (",
    )

    code_analysis_keywords = (
        "analyze this code",
        "analyse this code",
        "explain this code",
        "trace this code",
        "debug this code",
        "find the bug",
        "expected output",
        "what does this code do",
    )

    if (
        any(marker in text for marker in code_markers)
        and any(
            keyword in text
            for keyword in code_analysis_keywords
        )
    ):
        return TaskType.CODE_ANALYSIS

    code_generation_keywords = (
        "write code",
        "generate code",
        "implement",
        "create a function",
        "write a function",
    )

    if any(
        keyword in text
        for keyword in code_generation_keywords
    ):
        return TaskType.CODE_GENERATION

    return TaskType.GENERAL

def select_model_for_task(
    task_type: TaskType,
    installed_models: list[str],
    default_model: str,
    model_stats: list[dict] | None = None,
    minimum_feedback: int = 3,
) -> str:
    preferred_models = {
        TaskType.CODE_ANALYSIS: "qwen2.5-coder:3b",
        TaskType.CODE_GENERATION: "qwen2.5-coder:3b",
        TaskType.IMAGE_ANALYSIS: "gemma3:4b",
        TaskType.SERVER_ADMIN: "qwen3.5:4b",
        TaskType.GITHUB: "qwen3.5:4b",
        TaskType.GENERAL: "qwen3.5:4b",
    }

    if model_stats:
        eligible_models = [
            record
            for record in model_stats
            if (
                record["model_used"] in installed_models
                and record["total_feedback"] >= minimum_feedback
            )
        ]

        if eligible_models:
            best_model = max(
                eligible_models,
                key=lambda record: (
                    record["success_rate"],
                    record["total_feedback"],
                ),
            )

            return best_model["model_used"]

    preferred_model = preferred_models.get(
        task_type,
        default_model,
    )

    if preferred_model in installed_models:
        return preferred_model

    if default_model in installed_models:
        return default_model

    if installed_models:
        return installed_models[0]

    return default_model