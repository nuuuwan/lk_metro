from lk_metro.GD.Point import Point


class HBDGeometryPathMixin:
    def route_segments(
        self,
        positions: dict[str, Point] | None = None,
    ) -> dict[str, list[list[Point]]]:
        positions = positions or self.layout()
        paths_by_route = {}
        for route in self.routes:
            paths = []
            for segment in self._segments_by_route[route.id]:
                stops = segment["stops"]
                for first, second in zip(stops, stops[1:]):
                    edge = self._edge_key(first, second)
                    ref_first, ref_second = self._edge_directions[edge]
                    is_ref = first == ref_first and second == ref_second
                    path = [positions[ref_first], positions[ref_second]]
                    route_ids = sorted(
                        self._edge_routes[edge], key=self._route_order.get
                    )
                    if len(route_ids) > 1:
                        offset_index = (
                            route_ids.index(route.id)
                            - (len(route_ids) - 1) / 2
                        )
                        path = self._offset_path(
                            path, offset_index * self.parallel_route_gap
                        )
                    paths.append(path if is_ref else list(reversed(path)))
            paths_by_route[route.id] = paths
        return paths_by_route
