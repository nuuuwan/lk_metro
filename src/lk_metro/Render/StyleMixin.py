from lk_metro.DiagramStyle import (
    PARALLEL_ROUTE_GAP,
    STATION_TICK_LENGTH,
    STATION_TICK_STROKE_WIDTH,
)


class StyleMixin:
    MAP_SUBTITLE = "PARALLEL GEOGRAPHIC MAP"
    DESCRIPTION_LINES = (
        "Routes follow the geographic positions of their stops,",
        "with shared corridors separated for clarity.",
    )
    STATION_TICK_LENGTH = STATION_TICK_LENGTH
    STATION_TICK_STROKE_WIDTH = STATION_TICK_STROKE_WIDTH
    ROUTE_CURVE_RADIUS = 1.5
    ROTATE_LABELS = True
    WARN_LABEL_OVERLAPS = False
    WARN_LABEL_OVERLAPS_TOLERANCE = 100.0
    LABEL_BASELINE_COMPENSATION = 0.25
    LABEL_DIRECTIONS = (
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
        (-1.0, 1.0),
        (-1.0, 0.0),
        (-1.0, -1.0),
        (0.0, -1.0),
        (1.0, -1.0),
    )
    DEFAULT_PARALLEL_ROUTE_GAP = PARALLEL_ROUTE_GAP
