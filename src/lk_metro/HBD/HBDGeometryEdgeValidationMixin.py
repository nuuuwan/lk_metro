import math


class HBDGeometryEdgeValidationMixin:
    def _edge_geometry_errors(
        self,
        positions: dict[str, list[float]],
    ) -> tuple[list[tuple[str, str, str]], list[str]]:
        errors = []
        edges = []
        for route in self.routes:
            if route.id in self._circle_routes:
                continue
            for segment in self._segments_by_route[route.id]:
                first, second = segment["stops"]
                edges.append((route.id, first, second))
                x_delta = positions[second][0] - positions[first][0]
                y_delta = positions[second][1] - positions[first][1]
                zero_length = math.isclose(x_delta, 0.0)
                zero_length = zero_length and math.isclose(y_delta, 0.0)
                octilinear = not zero_length and (
                    math.isclose(x_delta, 0.0)
                    or math.isclose(y_delta, 0.0)
                    or math.isclose(abs(x_delta), abs(y_delta))
                )
                if not octilinear:
                    errors.append(
                        self._edge_geometry_error(
                            route.id,
                            first,
                            second,
                            x_delta,
                            y_delta,
                            positions,
                        )
                    )
        return edges, errors
