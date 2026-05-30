from enum import StrEnum

from pydantic import BaseModel, Field


class LegacySourceType(StrEnum):
    ERP_ORDER = "ERP_ORDER"
    PDM_PART = "PDM_PART"
    GROUPWARE_USER = "GROUPWARE_USER"


class LegacyContextSource(BaseModel):
    type: LegacySourceType
    id: str = Field(min_length=1, max_length=100)
