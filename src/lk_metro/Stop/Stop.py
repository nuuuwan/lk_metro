from dataclasses import dataclass
from typing import ClassVar

from ..AbstractData import AbstractData
from .StopReadMixin import StopReadMixin
from .StopXYMixin import StopXYMixin


@dataclass
class Stop(StopReadMixin, StopXYMixin, AbstractData):
    DATA_FILE: ClassVar[str] = "stops.json"
    name: str
    latlng: list[float]
    xy: list[float]
