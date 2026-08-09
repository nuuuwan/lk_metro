from typing import ClassVar


class HBDStyleMixin:
    DATA_FILE: ClassVar[str] = "harry_beck.json"
    UNIT_SCALE: ClassVar[float] = 8.0
    MAP_PADDING = 12
    LABEL_CANVAS_PADDING = MAP_PADDING / 2
    MAP_TITLE = "Lanka Metro Transit"
    TITLE_HEIGHT = 16
    LOGO_WIDTH = 28
    SHOW_LEGEND = True
    SHOW_DESCRIPTION = True
    LEGEND_WIDTH = 0
    LEGEND_LINE_HEIGHT = 3.5
    LEGEND_FONT_SIZE = 1.55
    DESCRIPTION_FONT_SIZE = 1.8
    DESCRIPTION_COLOR = "#777777"
    INFO_PANEL_COLOR = "#f7f7f7"
    INFO_PANEL_PADDING = 1.5
    TITLE_FONT_SIZE = 1.5
    BACKGROUND_COLOR = "#ffffff"
    WATER_FEATURE_COLOR = "#e8f8fc"
    GREEN_SPACE_COLOR = "#eefae8"
    GREEN_SPACE_LABEL_COLOR = "#4f7d47"
    GREEN_SPACE_LABEL_FONT_SIZE = 1
    TEXT_COLOR = "#991f1d"
    FONT_FAMILY = (
        "'Johnston Sans', 'Johnston 100', Johnston100, "
        "'Gill Sans', sans-serif"
    )
    SHOW_GRID = True
    CIRCLE_MIN_STOP_GAP_DEGREES = 20.0
    ROUTE_STROKE_WIDTH = 1.0
    FEATURE_CORNER_RADIUS = 1.5
    FORCE_45_DEGREE_LINES = True
    SHOW_PARALLEL_LINES = True
    PARALLEL_ROUTE_GAP = ROUTE_STROKE_WIDTH + 0.2
    PARALLEL_ROUTE_ORDER_OVERRIDES = (("CM02", "CM04"),)
    INTERCHANGE_RADIUS = 1.014
    INTERCHANGE_STROKE_WIDTH = 0.34
    LABEL_FONT_SIZE = 1.8
    ROUTE_NAME_FONT_SIZE = 3.2
    WARN_LABEL_OVERLAPS = True
    LABEL_OFFSET = 0.95
    LABEL_HALO_WIDTH = 0.2
    LABEL_COLLISION_PADDING = 0.3
    STATION_RADIUS = 0.52
    STATION_TICK_LENGTH = LABEL_FONT_SIZE / 4
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
