import math

from lk_metro.GD.Point import Point
from lk_metro.Render.Types import Bounds


class HBDTickOrientationMixin:
    def _orient_station_ticks(
        self,
        ticks: dict[str, tuple[Point, Point]],
        positions: dict[str, Point],
    ) -> dict[str, tuple[Point, Point]]:
        oriented = {
            stop_name: self._center_station_tick(tick, positions[stop_name])
            for stop_name, tick in ticks.items()
        }
        self._station_ticks = oriented
        for stop_name, tick in oriented.items():
            self._place_label_above_tick(stop_name, tick)
        self._finalize_stop_labels(
            list(self._stop_label_bounds_by_name.values())
        )
        return oriented

    def _center_station_tick(
        self,
        tick: tuple[Point, Point],
        position: Point,
    ) -> tuple[Point, Point]:
        x_delta = tick[1][0] - tick[0][0]
        y_delta = tick[1][1] - tick[0][1]
        scale = self.STATION_TICK_LENGTH / (2 * math.hypot(x_delta, y_delta))
        x_offset = x_delta * scale
        y_offset = y_delta * scale
        return (
            (position[0] - x_offset, position[1] - y_offset),
            (position[0] + x_offset, position[1] + y_offset),
        )

    def _place_label_above_tick(
        self,
        stop_name: str,
        tick: tuple[Point, Point],
    ) -> None:
        font_size = self._label_font_size(stop_name)
        half_width = self._label_width(stop_name, font_size) / 2
        half_height = self._label_half_height(stop_name, font_size)
        label_x = (tick[0][0] + tick[1][0]) / 2
        label_y = min(tick[0][1], tick[1][1])
        label_y -= half_height + self.LABEL_HALO_WIDTH
        self._stop_label_placements[stop_name] = (label_x, label_y, "middle")
        self._stop_label_bounds_by_name[stop_name] = (
            label_x - half_width,
            label_y - half_height,
            label_x + half_width,
            label_y + half_height,
        )

    def _tick_to_label(
        self,
        tick: tuple[Point, Point],
        position: Point,
        label_position: Point,
        label_bounds: Bounds,
    ) -> tuple[Point, Point]:
        label_edge = self._label_edge(position, label_position, label_bounds)
        opposite = position
        if position not in tick:
            label_vector = (
                label_edge[0] - position[0],
                label_edge[1] - position[1],
            )
            vector_length = self._point_length(label_vector)
            opposite_length = self.STATION_TICK_LENGTH - vector_length
            opposite = (
                position[0]
                - label_vector[0] / vector_length * opposite_length,
                position[1]
                - label_vector[1] / vector_length * opposite_length,
            )
        return opposite, label_edge

    @staticmethod
    def _point_length(point: Point) -> float:
        return (point[0] ** 2 + point[1] ** 2) ** 0.5

    @staticmethod
    def _label_edge(
        position: Point,
        label_position: Point,
        bounds: Bounds,
    ) -> Point:
        x_delta = label_position[0] - position[0]
        y_delta = label_position[1] - position[1]
        fractions = []
        if x_delta:
            fractions.append(
                min(
                    (bounds[0] - position[0]) / x_delta,
                    (bounds[2] - position[0]) / x_delta,
                )
            )
        if y_delta:
            fractions.append(
                min(
                    (bounds[1] - position[1]) / y_delta,
                    (bounds[3] - position[1]) / y_delta,
                )
            )
        fraction = max(fractions)
        return (
            position[0] + fraction * x_delta,
            position[1] + fraction * y_delta,
        )
