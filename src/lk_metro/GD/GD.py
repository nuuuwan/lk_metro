from lk_metro.GD.GDIOMixin import GDIOMixin
from lk_metro.GD.GDLayoutMixin import GDLayoutMixin
from lk_metro.GD.GDLegendMixin import GDLegendMixin
from lk_metro.GD.GDStopsMixin import GDStopsMixin
from lk_metro.GD.GDStyleMixin import GDStyleMixin
from lk_metro.GD.GDSvgMixin import GDSvgMixin
from lk_metro.GD.GDValidationMixin import GDValidationMixin
from lk_metro.Route import Route
from lk_metro.Stop.Stop import Stop


class GD(
    GDStyleMixin,
    GDLayoutMixin,
    GDLegendMixin,
    GDIOMixin,
    GDStopsMixin,
    GDSvgMixin,
    GDValidationMixin,
):
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
