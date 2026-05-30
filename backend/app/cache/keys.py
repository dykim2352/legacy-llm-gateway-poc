import hashlib
import json
from typing import Any


def build_chat_cache_key(prompt: str, context: dict[str, Any]) -> str:
    canonical_payload = json.dumps(
        {"prompt": prompt, "context": context},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    return f"llm_gateway:chat:{digest}"
