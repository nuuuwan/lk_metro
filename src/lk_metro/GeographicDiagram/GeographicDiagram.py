from ..DiagramStyle import (INTERCHANGE_RADIUS, INTERCHANGE_STROKE_WIDTH,
                            LABEL_FONT_SIZE, LABEL_OFFSET, ROUTE_STROKE_WIDTH,
                            STATION_TICK_LENGTH, STATION_TICK_STROKE_WIDTH)
from ..Route import Route
from ..Stop import Stop
from .GeographicDiagramLayoutMixin import GeographicDiagramLayoutMixin
from .GeographicDiagramLegendMixin import GeographicDiagramLegendMixin
from .GeographicDiagramStopsMixin import GeographicDiagramStopsMixin
from .GeographicDiagramSvgMixin import GeographicDiagramSvgMixin
from .GeographicDiagramValidationMixin import GeographicDiagramValidationMixin


class GeographicDiagram(
    GeographicDiagramLayoutMixin,
    GeographicDiagramLegendMixin,
    GeographicDiagramStopsMixin,
    GeographicDiagramSvgMixin,
    GeographicDiagramValidationMixin,
):
    MAP_TITLE = "Lanka Metro"
    MAP_SUBTITLE = "GEOGRAPHIC MAP"
    DESCRIPTION_LINES = (
        "Routes follow the geographic positions of their stops,",
        "preserving the network's real-world shape and orientation.",
    )
    FOOTER_TEXT = "Data from https://lankametro.lk · Design and Visualisation by https://github.com/nuuuwan"
    LEGEND_TITLE = "Routes"
    TITLE_HEIGHT = 12
    LOGO_WIDTH = 36
    LOGO_ASPECT_RATIO = 607 / 190
    LEGEND_WIDTH = 58
    LEGEND_LINE_HEIGHT = 3.5
    LEGEND_FONT_SIZE = 1.55
    TITLE_FONT_SIZE = 3.8
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

    def __init__(
        self,
        routes: list[Route],
        stops: list[Stop],
        width: int = 100,
        height: int = 100,
        padding: int = 6,
    ) -> None:
        if width <= padding * 2 or height <= padding * 2:
            raise ValueError(
                "width and height must be larger than twice the padding"
            )
        self.routes = routes
        self.legend_routes = routes
        self.stops = stops
        self.width = width
        self.height = height
        self.padding = padding
        self._stops_by_name = {stop.name: stop for stop in stops}
        self._validate_data()

    def route_paths(
        self, positions: dict[str, tuple[float, float]] | None = None
    ) -> dict[str, list[tuple[float, float]]]:
        positions = positions or self.layout()
        return {
            route.id: [positions[station] for station in route.stops]
            for route in self.routes
        }

    def to_svg(self) -> str:
        positions = self.layout()
        paths = self.route_paths(positions)
        lines = self._svg_header_lines()
        lines.extend(self._route_svg_lines(paths))
        lines.extend(self._stop_svg_lines(positions, paths))
        lines.extend(
            ["</g>", *self._title_and_legend_svg_lines(), "</g>", "</svg>"]
        )
        return "\n".join(lines) + "\n"
