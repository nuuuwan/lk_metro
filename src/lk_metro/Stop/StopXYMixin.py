from typing import ClassVar

from lk_metro.Stop.StopXYBuildMixin import StopXYBuildMixin
from lk_metro.Stop.StopXYIOMixin import StopXYIOMixin


class StopXYMixin(StopXYBuildMixin, StopXYIOMixin):
    DATA_FILE: ClassVar[str]
    XY_DATA_FILE: ClassVar[str] = "stops.xy.json"
    OVERLAPS_DATA_FILE: ClassVar[str] = "overlaps.json"
    XY_WIDTH: ClassVar[int] = 100
    XY_HEIGHT: ClassVar[int] = 100
    XY_PADDING: ClassVar[int] = 12
