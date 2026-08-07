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
        self._stop_label_bounds_by_name = {}
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
            route_segments = (
                segments if len(memberships[stop_name]) > 1 else {}
            )
            scores = [
                self._label_option_score(option, occupied, route_segments)
                for option in options
            ]
            selected = options[
                min(range(len(options)), key=scores.__getitem__)
            ]
            occupied.append(selected[0])
            self._stop_label_bounds_by_name[stop_name] = selected[0]
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
        segments: dict[str, list[list[Point]]],
    ) -> tuple[int, int, int, float, float]:
        bounds = option[0]
        overlaps = [self._overlap_area(bounds, other) for other in occupied]
        route_padding = self.ROUTE_STROKE_WIDTH / 2
        route_bounds = (
            bounds[0] - route_padding,
            bounds[1] - route_padding,
            bounds[2] + route_padding,
            bounds[3] + route_padding,
        )
        route_overlaps = sum(
            any(
                self._segment_intersects_bounds(first, second, route_bounds)
                for path in route_segments
                for first, second in zip(path, path[1:])
            )
            for route_segments in segments.values()
        )
        label_overlaps = sum(area > 0 for area in overlaps)
        canvas = (0.0, 0.0, float(self.width), float(self.height))
        return (
            route_overlaps + label_overlaps,
            route_overlaps,
            label_overlaps,
            sum(overlaps),
            self._outside_area(bounds, canvas),
        )

    def _stop_label_placement(
        self,
        stop_name: str,
        _position: Point,
    ) -> tuple[float, float, str]:
        return self._stop_label_placements[stop_name]
