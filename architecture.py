from pydantic import BaseModel, ConfigDict
from typing import List


class Component(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    technology: str


class ArchitecturePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_type: str
    components: List[Component]
    files: List[str]
    data_flow: List[str]
    dependencies: List[str]
    implementation_steps: List[str]