from lk_metro.GD.Point import Point
from lk_metro.PGD.PGDTypes import Edge


class PGDRouteBuildMixin:
    def _build_edge_routes(self) -> dict[Edge, list[str]]:
        edge_routes: dict[Edge, list[str]] = {}
        for route in self.routes:
            for first, second in zip(route.stops, route.stops[1:]):
                edge = self._edge_key(first, second)
                if edge not in edge_routes:
                    edge_routes[edge] = []
                    self._edge_directions[edge] = (first, second)
                edge_routes[edge].append(route.id)
        return edge_routes

    def _route_edge_path(
        self,
        first_name: str,
        second_name: str,
        first_point: Point,
        second_point: Point,
        route_id: str,
    ) -> list[Point]:
        edge = self._edge_key(first_name, second_name)
        route_ids = sorted(self._edge_routes[edge], key=self._route_order.get)
        reference_first, reference_second = self._edge_directions[edge]
        is_ref = (
            first_name == reference_first and second_name == reference_second
        )
        canonical = (
            (first_point, second_point)
            if is_ref
            else (second_point, first_point)
        )
        path = self._octilinear_path(*canonical)
        if len(route_ids) > 1:
            offset_index = (
                route_ids.index(route_id) - (len(route_ids) - 1) / 2
            )
            path = self._offset_path(
                path, offset_index * self.parallel_route_gap
            )
        return path if is_ref else list(reversed(path))
