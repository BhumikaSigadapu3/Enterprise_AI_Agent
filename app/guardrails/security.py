import re
from dataclasses import dataclass


INJECTION_PATTERNS = [
    r"ignore (all|any|previous|prior) instructions",
    r"system prompt",
    r"reveal .*instructions",
    r"developer message",
    r"jailbreak",
    r"do not follow",
]


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""


def validate_input(text: str) -> GuardrailResult:
    normalized = text.lower().strip()

    if len(normalized) < 3:
        return GuardrailResult(False, "Task is too short.")

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            return GuardrailResult(
                False,
                "Potential prompt injection detected. Please provide a normal task request."
            )

    return GuardrailResult(True)


def validate_tool_permission(tool_name: str, allowed_tools: list[str]) -> GuardrailResult:
    if tool_name not in allowed_tools:
        return GuardrailResult(False, f"Tool '{tool_name}' is not permitted for this request.")
    return GuardrailResult(True)


def validate_output(answer: str) -> GuardrailResult:
    if not answer or len(answer.strip()) < 2:
        return GuardrailResult(False, "Generated answer is empty.")
    return GuardrailResult(True)
