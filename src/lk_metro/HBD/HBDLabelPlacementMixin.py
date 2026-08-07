from lk_metro.GD.Point import Point
from lk_metro.HBD.HBDLabelCandidatesMixin import (HBDLabelCandidatesMixin,
                                                  LabelOption)
from lk_metro.HBD.HBDLabelPriorityMixin import HBDLabelPriorityMixin
from lk_metro.Render.Types import Bounds


class HBDLabelPlacementMixin(
    HBDLabelPriorityMixin,
    HBDLabelCandidatesMixin,
):
    def _prepare_stop_labels(
        self,
        positions: dict[str, Point],
        segments: dict[str, list[list[Point]]],
        memberships: dict[str, set[str]],
    ) -> None:
        occupied = []
        prefer_positive = True
        self._stop_label_placements = {}
        self._stop_label_bounds_by_name = {}
        stop_names = self._ordered_stop_names(positions, memberships)
        for stop_name in stop_names:
            options = self._side_label_options(
                stop_name,
                positions[stop_name],
                segments,
                memberships[stop_name],
                prefer_positive,
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
            prefer_positive = not prefer_positive
        self._stop_label_bounds = occupied

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
        edge = self.LABEL_CANVAS_PADDING
        canvas = (edge, edge, self.width - edge, self.height - edge)
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
