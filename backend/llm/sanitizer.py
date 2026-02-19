from __future__ import annotations

import json
import re
from typing import Any


CONTROL_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
PROMPT_INJECTION_HINTS = [
    "ignore previous instructions",
    "system prompt",
    "developer message",
    "act as",
    "jailbreak",
]


def _truncate(value: str, max_length: int = 1500) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."


def sanitize_text(value: Any, max_length: int = 1500) -> str:
    raw = "" if value is None else str(value)
    cleaned = CONTROL_PATTERN.sub(" ", raw)
    lowered = cleaned.lower()
    for token in PROMPT_INJECTION_HINTS:
        lowered = lowered.replace(token, "[redacted-instruction]")
    if lowered != cleaned.lower():
        cleaned = lowered
    return _truncate(cleaned.strip(), max_length=max_length)


def sanitize_context_items(context: list[dict[str, Any]], max_items: int = 10) -> list[dict[str, Any]]:
    output = []
    for item in context[:max_items]:
        safe_item = {}
        for key, value in item.items():
            safe_key = sanitize_text(key, max_length=64)
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            safe_item[safe_key] = sanitize_text(value)
        output.append(safe_item)
    return output

