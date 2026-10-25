from pydantic import BaseModel, ConfigDict
from typing import List


class ImpactItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str
    reason: str


class ImpactReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    directly_affected: List[ImpactItem]
    indirectly_affected: List[ImpactItem]