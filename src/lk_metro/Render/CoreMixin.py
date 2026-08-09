from lk_metro.DiagramStyle import PARALLEL_ROUTE_GAP
from lk_metro.GD.Point import Point
from lk_metro.Render.RouteGeometryMixin import RouteGeometryMixin
from lk_metro.Route import Route
from lk_metro.Stop.Stop import Stop


class CoreMixin:
    def _base_route_edge_path(
        self, first: Point, second: Point
    ) -> list[Point]:
        return RouteGeometryMixin.octilinear_path(first, second)

    def __init__(
        self,
        routes: list[Route],
        stops: list[Stop],
        width: int = 200,
        height: int = 200,
        padding: int = 6,
        parallel_route_gap: float = PARALLEL_ROUTE_GAP,
    ) -> None:
        if parallel_route_gap <= 0:
            raise ValueError("parallel_route_gap must be positive")
        super().__init__(
            routes, stops, width, height, padding, parallel_route_gap
        )
        active_stop_names = {
            name for route in self.routes for name in route.stops
        }
        self.stops = [
            stop for stop in self.stops if stop.name in active_stop_names
        ]

    def layout(self) -> dict[str, Point]:
        positions = {
            stop.name: (stop.xy[0], stop.xy[1]) for stop in self.stops
        }
        min_x = min(point[0] for point in positions.values())
        max_x = max(point[0] for point in positions.values())
        min_y = min(point[1] for point in positions.values())
        max_y = max(point[1] for point in positions.values())
        x_scale = (self.width - self.padding * 2) / (max_x - min_x)
        y_scale = (self.height - self.padding * 2) / (max_y - min_y)
        return {
            name: (
                self.padding + (point[0] - min_x) * x_scale,
                self.padding + (point[1] - min_y) * y_scale,
            )
            for name, point in positions.items()
        }

    def route_segments(
        self,
        positions: dict[str, Point] | None = None,
    ) -> dict[str, list[list[Point]]]:
        positions = positions or self.layout()
        return {
            route.id: [
                self._route_edge_path(
                    first,
                    second,
                    positions[first],
                    positions[second],
                    route.id,
                )
                for first, second in zip(route.stops, route.stops[1:])
            ]
            for route in self.routes
        }

    def to_svg(self) -> str:
        positions = self.layout()
        segments = self.route_segments(positions)
        memberships = self._route_memberships()
        lines = self._svg_header_lines()
        lines.extend(self._route_svg_lines(segments))
        self._prepare_stop_labels(positions, segments, memberships)
        self.station_ticks(positions, segments, memberships)
        self._prepare_route_names(segments)
        lines.extend(self._stop_marker_svg_lines(positions, memberships))
        lines.extend(self._route_name_svg_lines())
        lines.extend(self._stop_label_svg_lines(positions))
        lines.extend(
            ["</g>", *self._title_and_legend_svg_lines(), "</g>", "</svg>"]
        )
        return "\n".join(lines) + "\n"
