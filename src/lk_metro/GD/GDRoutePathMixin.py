class GDRoutePathMixin:
    def route_paths(
        self, positions: dict[str, tuple[float, float]] | None = None
    ) -> dict[str, list[tuple[float, float]]]:
        positions = positions or self.layout()
        return {
            route.id: [positions[station] for station in route.stops]
            for route in self.routes
        }

    def _base_route_edge_path(
        self,
        first: tuple[float, float],
        second: tuple[float, float],
    ) -> list[tuple[float, float]]:
        return [first, second]

    def route_segments(
        self, positions: dict[str, tuple[float, float]] | None = None
    ) -> dict[str, list[list[tuple[float, float]]]]:
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

    @staticmethod
    def _route_path_data(
        segments: list[list[tuple[float, float]]],
    ) -> str:
        points = []
        for segment in segments:
            if points and points[-1] != segment[0]:
                points.append(
                    (
                        (points[-1][0] + segment[0][0]) / 2,
                        (points[-1][1] + segment[0][1]) / 2,
                    )
                )
                points.extend(segment)
            elif points:
                points.extend(segment[1:])
            else:
                points.extend(segment)
        commands = [f"M {points[0][0]},{points[0][1]}"]
        commands.extend(f"L {x},{y}" for x, y in points[1:])
        return " ".join(commands)
