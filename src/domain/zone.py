from .enums import ZoneType
from pydantic import BaseModel, Field


class Zone(BaseModel):
    name: str
    x: int
    y: int
    zone_type: ZoneType = Field(default=ZoneType.NORMAL)
    color: str = Field(default="white")
    max_drones: int = Field(default=1)
