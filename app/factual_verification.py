import re


CORRECTION_PATTERNS = (
    r"\bwrong\b",
    r"\bincorrect\b",
    r"\bthat's wrong\b",
    r"\bthats wrong\b",
    r"\byou are wrong\b",
    r"\byou're wrong\b",
    r"\bare you sure\b",
    r"\bverify\b",
    r"\bfact[- ]?check\b",
    r"\bcheck that\b",
    r"\blook it up\b",
    r"\bsource please\b",
    r"\bdo you know who\b",
    r"\bdo u know who\b",
)

FACT_LOOKUP_PATTERNS = (
    r"^\s*who\s+(is|was|are|were)\b",
    r"^\s*who\s+(plays|played)\b",
    r"^\s*who's\b",
    r"^\s*what\s+is\s+the\s+(name|identity)\b",
    r"^\s*when\s+(did|was|is|were)\b",
    r"^\s*where\s+(is|was|are|were)\b",
    r"^\s*which\s+(episode|season|person|actor|character)\b",
    r"^\s*how\s+old\s+\b",
    r"^\s*how\s+many\s+(episodes|seasons)\b",
    r"^\s*(wasn't|wasnt|isn't|isnt|weren't|werent)\b",
    r"^\s*(didn't|didnt|doesn't|doesnt)\b",
)

MAX_VERIFICATION_QUERY_CHARS = 600


def is_correction_or_verification_request(
    message: str,
) -> bool:
    normalized = " ".join(
        message.lower().split()
    )

    return any(
        re.search(pattern, normalized)
        for pattern in CORRECTION_PATTERNS
    )


def is_fact_lookup_question(
    message: str,
) -> bool:
    normalized = " ".join(
        message.lower().split()
    )

    return any(
        re.search(pattern, normalized)
        for pattern in FACT_LOOKUP_PATTERNS
    )


def should_auto_verify(
    message: str,
) -> bool:
    return (
        is_fact_lookup_question(message)
        or is_correction_or_verification_request(
            message
        )
    )


def build_verification_query(
    message: str,
    history: list[dict],
) -> str:
    user_messages = [
        " ".join(
            str(item.get("content", "")).split()
        )
        for item in history
        if item.get("role") == "user"
        and str(
            item.get("content", "")
        ).strip()
    ]

    current = " ".join(
        message.split()
    )

    if (
        not user_messages
        or user_messages[-1] != current
    ):
        user_messages.append(current)

    context = user_messages[-4:]

    query = " | ".join(context)

    if len(query) > MAX_VERIFICATION_QUERY_CHARS:
        query = query[
            -MAX_VERIFICATION_QUERY_CHARS:
        ]

    return query.strip()
