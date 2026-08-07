from datetime import datetime

from lk_metro.DiagramStyle import (
    INTERCHANGE_RADIUS,
    INTERCHANGE_STROKE_WIDTH,
    LABEL_FONT_SIZE,
    LABEL_OFFSET,
    ROUTE_STROKE_WIDTH,
    STATION_TICK_LENGTH,
    STATION_TICK_STROKE_WIDTH,
)


class GDStyleMixin:
    MAP_TITLE = "Lanka Metro"
    DESCRIPTION_LINES = (
        "Routes follow the geographic positions of their stops,",
        "with shared corridors separated for clarity.",
    )
    FOOTER_TEXT = (
        "Data from https://lankametro.lk · Design and Visualisation by "
        "https://github.com/nuuuwan"
    )
    MAP_VERSION = datetime.now().strftime("v%Y-%m-%d %H:%M")
    LEGEND_TITLE = "Routes"
    TITLE_HEIGHT = 12
    LOGO_WIDTH = 36
    LOGO_ASPECT_RATIO = 607 / 190
    LEGEND_WIDTH = 58
    LEGEND_LINE_HEIGHT = 3.5
    LEGEND_FONT_SIZE = 1.55
    FOOTER_FONT_SIZE = 1.0
    TITLE_FONT_SIZE = 10
    BACKGROUND_COLOR = "#ffffff"
    TEXT_COLOR = "#991f1d"
    LABEL_COLOR = "#000000"
    FONT_FAMILY = "sans-serif"
    SHOW_GRID = False
    ROUTE_STROKE_WIDTH = ROUTE_STROKE_WIDTH
    INTERCHANGE_RADIUS = INTERCHANGE_RADIUS
    INTERCHANGE_STROKE_WIDTH = INTERCHANGE_STROKE_WIDTH
    STATION_TICK_LENGTH = STATION_TICK_LENGTH
    STATION_TICK_STROKE_WIDTH = STATION_TICK_STROKE_WIDTH
    LABEL_FONT_SIZE = LABEL_FONT_SIZE
    LABEL_OFFSET = LABEL_OFFSET
    LABEL_HALO_WIDTH = 0.0
