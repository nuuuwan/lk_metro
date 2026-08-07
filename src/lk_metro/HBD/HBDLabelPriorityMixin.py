import math

from lk_metro.GD.Point import Point


class HBDLabelPriorityMixin:
    CONGESTION_MIN_NEIGHBORS = 7
    CONGESTION_RADIUS_STEPS = 2

    def _ordered_stop_names(
        self,
        positions: dict[str, Point],
        memberships: dict[str, set[str]],
    ) -> list[str]:
        stop_names = [stop.name for stop in self.stops]
        congestion = {
            name: sum(
                math.dist(positions[name], positions[other])
                <= self.UNIT_SCALE * self.CONGESTION_RADIUS_STEPS
                for other in stop_names
                if other != name
            )
            for name in stop_names
        }
        return sorted(
            stop_names,
            key=lambda name: self._label_priority(
                name, memberships, congestion[name]
            ),
        )

    def _label_priority(
        self,
        stop_name: str,
        memberships: dict[str, set[str]],
        congestion: int,
    ) -> tuple[int, int, str]:
        if self._is_terminus(stop_name):
            tier = 0
        elif len(memberships[stop_name]) > 1:
            tier = 1
        elif congestion >= self.CONGESTION_MIN_NEIGHBORS:
            tier = 2
        else:
            tier = 3
        return tier, -congestion, stop_name
