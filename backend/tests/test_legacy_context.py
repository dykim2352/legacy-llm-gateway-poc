from typing import Any

from app.legacy.context import LegacyContextBuilder, build_prompt
from app.legacy.models import LegacyContextSource, LegacySourceType


class FakeLegacyClient:
    async def fetch_source(
        self,
        source: LegacyContextSource,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if source.id == "MISSING":
            return None, f"[WARN] {source.type.value} {source.id} not found"
        return {
            "id": source.id,
            "itemName": "Tactical Network Module",
            "roles": ["USER", "APPROVER"],
        }, None


def test_legacy_context_builder_formats_selected_sources() -> None:
    context = _run_async(
        LegacyContextBuilder(FakeLegacyClient()).build_context(
            [LegacyContextSource(type=LegacySourceType.ERP_ORDER, id="ORD-1001")]
        )
    )

    assert "[ERP_ORDER]" in context
    assert "id: ORD-1001" in context
    assert "itemName: Tactical Network Module" in context
    assert "- APPROVER" in context


def test_legacy_context_builder_keeps_warning_on_lookup_failure() -> None:
    context = _run_async(
        LegacyContextBuilder(FakeLegacyClient()).build_context(
            [LegacyContextSource(type=LegacySourceType.PDM_PART, id="MISSING")]
        )
    )

    assert context == "[WARN] PDM_PART MISSING not found"


def test_build_prompt_adds_legacy_and_manual_context() -> None:
    prompt = build_prompt(
        "Summarize risk",
        "[ERP_ORDER]\norderId: ORD-1001",
        {"requester": "mock-user"},
    )

    assert "Summarize risk" in prompt
    assert "[ERP_ORDER]" in prompt
    assert "[MANUAL_CONTEXT]" in prompt
    assert "requester: mock-user" in prompt


def _run_async(awaitable: Any) -> Any:
    import asyncio

    return asyncio.run(awaitable)
