from typing import ClassVar


class HBDStyleMixin:
    DATA_FILE: ClassVar[str] = "harry_beck.json"
    UNIT_SCALE: ClassVar[float] = 8.0
    MAP_PADDING = 12
    LABEL_CANVAS_PADDING = MAP_PADDING / 2
    MAP_TITLE = "LANKA METRO"
    TITLE_HEIGHT = 12
    LOGO_WIDTH = 36
    SHOW_LEGEND = True
    SHOW_DESCRIPTION = True
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
    SHOW_GRID = True
    CIRCLE_MIN_STOP_GAP_DEGREES = 20.0
    ROUTE_STROKE_WIDTH = 1.0
    FORCE_45_DEGREE_LINES = True
    SHOW_PARALLEL_LINES = True
    PARALLEL_ROUTE_GAP = ROUTE_STROKE_WIDTH + 0.2
    PARALLEL_ROUTE_ORDER_OVERRIDES = (("CM02", "CM04"),)
    INTERCHANGE_RADIUS = 1.014
    INTERCHANGE_STROKE_WIDTH = 0.34
    LABEL_FONT_SIZE = 0.9
    ROUTE_NAME_FONT_SIZE = 3.2
    WARN_LABEL_OVERLAPS = True
    LABEL_OFFSET = 0.95
    LABEL_HALO_WIDTH = 0.2
    STATION_RADIUS = 0.52
    STATION_TICK_LENGTH = LABEL_FONT_SIZE / 2
    STATION_TICK_STROKE_WIDTH = 0.42
    ROTATE_LABELS = False
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
