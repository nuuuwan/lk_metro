from lk_metro.GD.Point import Point


class HBDTickOrientationMixin:
    def _orient_station_ticks(
        self,
        ticks: dict[str, tuple[Point, Point]],
        positions: dict[str, Point],
    ) -> dict[str, tuple[Point, Point]]:
        return {
            name: self._tick_toward_label(
                tick,
                positions[name],
                self._stop_label_placements[name][:2],
            )
            for name, tick in ticks.items()
        }

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
