from dataclasses import dataclass
from typing import ClassVar

from .AbstractData import AbstractData


@dataclass
class Stop(AbstractData):
	DATA_FILE: ClassVar[str] = "stops.json"

	name: str
	latlng: list[float]
