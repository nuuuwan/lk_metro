from typing import ClassVar


class HarryBeckDiagramStyleMixin:
    DATA_FILE: ClassVar[str] = "harry_beck.json"
    UNIT_SCALE: ClassVar[float] = 8.0
    MAP_TITLE = "LANKA METRO"
    TITLE_HEIGHT = 12
    LOGO_WIDTH = 36
    LEGEND_WIDTH = 0
    LEGEND_LINE_HEIGHT = 3.5
    LEGEND_FONT_SIZE = 1.55
    TITLE_FONT_SIZE = 3.8
    BACKGROUND_COLOR = "#ffffff"
    TEXT_COLOR = "#991f1d"
    FONT_FAMILY = (
        "'Johnston Sans', 'Johnston 100', Johnston100, "
        "'Gill Sans', sans-serif"
    )
    SHOW_GRID = False
    ROUTE_STROKE_WIDTH = 1.0
    PARALLEL_ROUTE_GAP = 1.0
    INTERCHANGE_RADIUS = 1.014
    INTERCHANGE_STROKE_WIDTH = 0.34
    LABEL_FONT_SIZE = 1.8
    TERMINAL_LABEL_FONT_SIZE = LABEL_FONT_SIZE
    ROUTE_NAME_FONT_SIZE = 3.2
    WARN_LABEL_OVERLAPS = True
    LABEL_OFFSET = 0.95
    LABEL_HALO_WIDTH = 0.2
    STATION_TICK_LENGTH = 0.58
    STATION_TICK_STROKE_WIDTH = 0.42
    ROTATE_LABELS = False
    RIVER_PATH = (
        "M -4,17 L 33,17 L 38,22 L 44,28 L 44,34 L 78,34 " "L 98,54 L 160,54"
    )
    ROUTE_NAME_POSITIONS: ClassVar[dict[str, tuple[float, float, float]]] = {
        "CM01": (110.0, 98.5, 0.0),
        "CM02": (126.0, 74.5, 0.0),
        "CM03": (58.0, 26.5, 0.0),
        "CM04": (108.0, 122.5, 0.0),
        "CM05": (94.0, 10.0, 0.0),
        "CM06": (8.5, 82.0, -90.0),
        "CM08": (78.0, 106.5, 0.0),
    }
    DIRECTIONS: ClassVar[tuple[str, ...]] = (
        "E",
        "SE",
        "S",
        "SW",
        "W",
        "NW",
        "N",
        "NE",
    )
    DIRECTION_VECTORS: ClassVar[tuple[tuple[int, int], ...]] = (
        (1, 0),
        (1, 1),
        (0, 1),
        (-1, 1),
        (-1, 0),
        (-1, -1),
        (0, -1),
        (1, -1),
    )
