from dataclasses import dataclass
from typing import ClassVar

from .AbstractData import AbstractData


@dataclass
class Route(AbstractData):
    DATA_FILE: ClassVar[str] = "routes.json"

    id: str
    name: str
    distance_km: float
    stops: list[str]
    color: str
