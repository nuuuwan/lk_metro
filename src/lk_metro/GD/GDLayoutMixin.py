import math


class GDLayoutMixin:
    def layout(self) -> dict[str, tuple[float, float]]:
        projected = {
            stop.name: (
                math.radians(stop.latlng[1]),
                math.log(
                    math.tan(math.pi / 4 + math.radians(stop.latlng[0]) / 2)
                ),
            )
            for stop in self.stops
        }
        min_x = min(point[0] for point in projected.values())
        max_x = max(point[0] for point in projected.values())
        min_y = min(point[1] for point in projected.values())
        max_y = max(point[1] for point in projected.values())
        x_range = max_x - min_x
        y_range = max_y - min_y
        if math.isclose(x_range, 0.0) or math.isclose(y_range, 0.0):
            raise ValueError(
                "Geographic stops must span both latitude and longitude"
            )
        scale = min(
            (self.width - self.padding * 2) / x_range,
            (self.height - self.padding * 2) / y_range,
        )
        x_offset = (
            self.padding
            + (self.width - self.padding * 2 - x_range * scale) / 2
        )
        y_offset = (
            self.padding
            + (self.height - self.padding * 2 - y_range * scale) / 2
        )
        self._mercator_bounds = (min_x, min_y, max_x, max_y)
        self._mercator_scale = scale
        self._mercator_offset = (x_offset, y_offset)
        return {
            name: (
                x_offset + (point[0] - min_x) * scale,
                y_offset + (max_y - point[1]) * scale,
            )
            for name, point in projected.items()
        }

    def _station_tick(
        self,
        stop_name: str,
        positions: dict[str, tuple[float, float]],
        paths: dict[str, list[tuple[float, float]]],
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        route = next(
            route for route in self.routes if stop_name in route.stops
        )
        stop_index = route.stops.index(stop_name)
        neighbor_index = 1 if stop_index == 0 else stop_index - 1
        neighbor = paths[route.id][neighbor_index]
        x_coordinate, y_coordinate = positions[stop_name]
        x_delta = neighbor[0] - x_coordinate
        y_delta = neighbor[1] - y_coordinate
        length = math.hypot(x_delta, y_delta)
        x_offset = -y_delta / length * self.STATION_TICK_LENGTH / 2
        y_offset = x_delta / length * self.STATION_TICK_LENGTH / 2
        return (
            (x_coordinate - x_offset, y_coordinate - y_offset),
            (x_coordinate + x_offset, y_coordinate + y_offset),
        )
