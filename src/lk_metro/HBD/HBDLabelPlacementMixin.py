from lk_metro.GD.Point import Point
from lk_metro.HBD.HBDLabelCandidatesMixin import (HBDLabelCandidatesMixin,
                                                  LabelOption)
from lk_metro.PGD.PGDTypes import Bounds


class HBDLabelPlacementMixin(HBDLabelCandidatesMixin):
    def _prepare_stop_labels(
        self,
        positions: dict[str, Point],
        segments: dict[str, list[list[Point]]],
        memberships: dict[str, set[str]],
    ) -> None:
        occupied = []
        self._stop_label_placements = {}
        stop_names = sorted(
            (stop.name for stop in self.stops),
            key=lambda name: self._label_priority(name, memberships),
        )
        for stop_name in stop_names:
            options = self._side_label_options(
                stop_name,
                positions[stop_name],
                segments,
                memberships[stop_name],
            )
            selected = min(
                options,
                key=lambda option: self._label_option_score(option, occupied),
            )
            occupied.append(selected[0])
            self._stop_label_placements[stop_name] = (*selected[1], "middle")
        self._stop_label_bounds = occupied

    def _label_priority(
        self,
        stop_name: str,
        memberships: dict[str, set[str]],
    ) -> int:
        is_terminus = any(
            stop_name in (route.stops[0], route.stops[-1])
            for route in self.routes
        )
        if is_terminus:
            return 0
        if len(memberships[stop_name]) > 1:
            return 1
        return 2

    def _label_option_score(
        self,
        option: LabelOption,
        occupied: list[Bounds],
    ) -> tuple[int, float, float]:
        bounds = option[0]
        overlaps = [self._overlap_area(bounds, other) for other in occupied]
        canvas = (0.0, 0.0, float(self.width), float(self.height))
        return (
            sum(area > 0 for area in overlaps),
            sum(overlaps),
            self._outside_area(bounds, canvas),
        )

    def _stop_label_placement(
        self,
        stop_name: str,
        position: Point,
    ) -> tuple[float, float, str]:
        return self._stop_label_placements[stop_name]
