from dataclasses import dataclass
from typing import ClassVar

from lk_metro.AbstractData import AbstractData
from lk_metro.Stop.StopReadMixin import StopReadMixin
from lk_metro.Stop.StopXYMixin import StopXYMixin


@dataclass
class Stop(StopReadMixin, StopXYMixin, AbstractData):
    DATA_FILE: ClassVar[str] = "stops.json"
    name: str
    latlng: list[float]
    xy: list[float]
