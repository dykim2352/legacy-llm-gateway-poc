from typing import Any

import httpx

from app.core.config import settings
from app.legacy.models import LegacyContextSource, LegacySourceType


class LegacyContextClient:
    def __init__(self, base_url: str | None = None) -> None:
        if base_url is None:
            base_url = settings.legacy_service_base_url
        self.base_url = base_url.rstrip("/")

    async def fetch_source(self, source: LegacyContextSource) -> tuple[dict[str, Any] | None, str | None]:
        path = self._path_for(source)
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            return None, f"[WARN] {source.type.value} {source.id} lookup failed: {exc}"

        if response.status_code == 404:
            return None, f"[WARN] {source.type.value} {source.id} not found"

        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return None, f"[WARN] {source.type.value} {source.id} lookup failed: {exc}"

        data = response.json()
        if not isinstance(data, dict):
            return None, f"[WARN] {source.type.value} {source.id} returned invalid data"

        return data, None

    @staticmethod
    def _path_for(source: LegacyContextSource) -> str:
        if source.type == LegacySourceType.ERP_ORDER:
            return f"/api/v1/legacy/erp/orders/{source.id}"
        if source.type == LegacySourceType.PDM_PART:
            return f"/api/v1/legacy/pdm/parts/{source.id}"
        return f"/api/v1/legacy/groupware/users/{source.id}"


def get_legacy_context_client() -> LegacyContextClient:
    return LegacyContextClient()
