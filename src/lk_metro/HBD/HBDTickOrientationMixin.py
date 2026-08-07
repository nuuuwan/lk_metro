from lk_metro.GD.Point import Point
from lk_metro.PGD.PGDTypes import Bounds


class HBDTickOrientationMixin:
    def _orient_station_ticks(
        self,
        ticks: dict[str, tuple[Point, Point]],
        positions: dict[str, Point],
    ) -> dict[str, tuple[Point, Point]]:
        return {
            name: self._tick_to_label(
                tick,
                positions[name],
                self._stop_label_placements[name][:2],
                self._stop_label_bounds_by_name[name],
            )
            for name, tick in ticks.items()
        }

    def _tick_to_label(
        self,
        tick: tuple[Point, Point],
        position: Point,
        label_position: Point,
        label_bounds: Bounds,
    ) -> tuple[Point, Point]:
        label_side = self._tick_toward_label(tick, position, label_position)[
            1
        ]
        opposite = position
        if position not in tick:
            opposite = tick[1] if tick[0] == label_side else tick[0]
        label_edge = self._label_edge(position, label_position, label_bounds)
        return opposite, label_edge

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

    @staticmethod
    def _tick_toward_label(
        tick: tuple[Point, Point],
        position: Point,
        label_position: Point,
    ) -> tuple[Point, Point]:
        outer = tick[1] if tick[1] != position else tick[0]
        reflected = (
            2 * position[0] - outer[0],
            2 * position[1] - outer[1],
        )
        label_vector = (
            label_position[0] - position[0],
            label_position[1] - position[1],
        )
        selected = max(
            (outer, reflected),
            key=lambda point: (
                (point[0] - position[0]) * label_vector[0]
                + (point[1] - position[1]) * label_vector[1]
            ),
        )
        return position, selected
