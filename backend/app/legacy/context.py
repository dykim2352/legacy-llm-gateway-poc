from typing import Any

from app.legacy.client import LegacyContextClient
from app.legacy.models import LegacyContextSource, LegacySourceType


class LegacyContextBuilder:
    def __init__(self, client: LegacyContextClient) -> None:
        self.client = client

    async def build_context(self, sources: list[LegacyContextSource]) -> str:
        blocks: list[str] = []
        for source in sources:
            data, warning = await self.client.fetch_source(source)
            if warning is not None:
                blocks.append(warning)
                continue
            if data is not None:
                blocks.append(_format_source_block(source.type, data))
        return "\n\n".join(blocks)


def build_prompt(prompt: str, legacy_context: str = "", manual_context: dict[str, Any] | None = None) -> str:
    context_parts: list[str] = []
    if legacy_context:
        context_parts.append(legacy_context)
    if manual_context:
        context_parts.append("[MANUAL_CONTEXT]\n" + _format_mapping(manual_context))
    if not context_parts:
        return prompt
    return f"{prompt}\n\nContext:\n" + "\n\n".join(context_parts)


def _format_source_block(source_type: LegacySourceType, data: dict[str, Any]) -> str:
    return f"[{source_type.value}]\n{_format_mapping(data)}"


def _format_mapping(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"- {item}" for item in value)
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for nested_key, nested_value in value.items():
                lines.append(f"  {nested_key}: {nested_value}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)
