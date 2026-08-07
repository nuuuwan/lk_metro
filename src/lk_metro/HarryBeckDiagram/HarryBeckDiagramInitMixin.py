from dataclasses import replace
from pathlib import Path

from ..Route import Route
from ..Stop import Stop


class HarryBeckDiagramInitMixin:
    def __init__(self, routes: list[Route], stops: list[Stop]) -> None:
        super().__init__(
            routes,
            stops,
            parallel_route_gap=self.PARALLEL_ROUTE_GAP,
        )
        self.legend_routes = routes
        self.design_path = Path(__file__).resolve().parents[3] / "data"
        self.design_path = self.design_path / self.DATA_FILE
        self._origin_positions, self._segments_by_route, designed_stops = (
            self._read_design()
        )
        self._apply_design(routes, stops, designed_stops)
        self._route_order = {
            route.id: index for index, route in enumerate(self.routes)
        }
        self._edge_directions = {}
        self._edge_routes = self._build_design_edge_routes()
        self._stop_numbers = {
            stop.name: [
                str(route.stops.index(stop.name) + 1)
                for route in self.routes
                if stop.name in route.stops
            ]
            for stop in self.stops
        }

    def _apply_design(
        self,
        routes: list[Route],
        stops: list[Stop],
        designed_stops_by_route: dict[str, list[str]],
    ) -> None:
        routes_by_id = {route.id: route for route in routes}
        self.routes = [
            replace(routes_by_id[route_id], stops=route_stops)
            for route_id, route_stops in designed_stops_by_route.items()
        ]
        designed_stop_names = {
            name
            for route_stops in designed_stops_by_route.values()
            for name in route_stops
        }
        stops_by_name = {stop.name: stop for stop in stops}
        self.stops = [
            stops_by_name.get(
                name, Stop(name=name, latlng=[0.0, 0.0], xy=[0.0, 0.0])
            )
            for name in designed_stop_names
        ]

    def _stop_label(self, stop_name: str) -> str:
        return stop_name

    def _label_lines(self, label: str) -> tuple[str, ...]:
        lines = []
        for word in label.split():
            if lines and len(lines[-1]) + len(word) + 1 <= 12:
                lines[-1] = f"{lines[-1]} {word}"
            else:
                lines.append(word)
        return tuple(lines)

    def _terminal_label_font_size(self) -> float:
        return self.TERMINAL_LABEL_FONT_SIZE

    def _route_name_font_size(self) -> float:
        return self.ROUTE_NAME_FONT_SIZE
