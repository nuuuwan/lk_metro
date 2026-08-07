from typing import ClassVar

from .StopXYBuildMixin import StopXYBuildMixin
from .StopXYIOMixin import StopXYIOMixin


class StopXYMixin(StopXYBuildMixin, StopXYIOMixin):
    DATA_FILE: ClassVar[str]
    XY_DATA_FILE: ClassVar[str] = "stops.xy.json"
    OVERLAPS_DATA_FILE: ClassVar[str] = "overlaps.json"
    XY_WIDTH: ClassVar[int] = 100
    XY_HEIGHT: ClassVar[int] = 100
    XY_PADDING: ClassVar[int] = 12
