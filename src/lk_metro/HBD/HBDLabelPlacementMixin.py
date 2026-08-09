from lk_metro.GD.Point import Point
from lk_metro.HBD.HBDLabelCandidatesMixin import (HBDLabelCandidatesMixin,
                                                  LabelOption)
from lk_metro.HBD.HBDLabelPriorityMixin import HBDLabelPriorityMixin
from lk_metro.Render.Types import Bounds

LabelScore = tuple[int, int, int, float, float]


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
        self._label_positions = positions
        self._label_segments = segments
        self._label_memberships = memberships
        self._stop_label_placements = {
            stop.name: (*positions[stop.name], "middle")
            for stop in self.stops
        }
        self._stop_label_bounds_by_name = {}
        for stop in self.stops:
            stop_name = stop.name
            position = positions[stop_name]
            font_size = self._label_font_size(stop_name)
            half_width = self._label_width(stop_name, font_size) / 2
            half_height = self._label_half_height(stop_name, font_size)
            self._stop_label_bounds_by_name[stop_name] = (
                position[0] - half_width,
                position[1] - half_height,
                position[0] + half_width,
                position[1] + half_height,
            )
        self._stop_label_bounds = list(
            self._stop_label_bounds_by_name.values()
        )

    def _finalize_stop_labels(self, occupied: list[Bounds]) -> None:
        self._stop_label_bounds = occupied
        self._write_cached_stop_labels()
        if self.WARN_LABEL_OVERLAPS:
            self._warn_label_overlaps(
                list(self._stop_label_bounds_by_name.items())
            )

    def _stop_label_candidates(
        self,
        stop_name: str,
        positions: dict[str, Point],
        segments: dict[str, list[list[Point]]],
        memberships: dict[str, set[str]],
        occupied: list[Bounds],
        prefer_positive: bool,
    ) -> tuple[list[LabelOption], list[LabelScore]]:
        options = self._side_label_options(
            stop_name,
            positions[stop_name],
            segments,
            memberships[stop_name],
            prefer_positive,
        )
        scores = [
            self._label_option_score(
                option, positions[stop_name], occupied, segments
            )
            for option in options
        ]
        return options, scores

    def _label_option_score(
        self,
        option: LabelOption,
        position: Point,
        occupied: list[Bounds],
        segments: dict[str, list[list[Point]]],
    ) -> LabelScore:
        bounds = option[0]
        padding = self.LABEL_COLLISION_PADDING
        collision_bounds = (
            bounds[0] - padding,
            bounds[1] - padding,
            bounds[2] + padding,
            bounds[3] + padding,
        )
        overlaps = [
            self._overlap_area(collision_bounds, other) for other in occupied
        ]
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
            route_overlaps,
            label_overlaps,
            self._point_length(
                (option[1][0] - position[0], option[1][1] - position[1])
            ),
            sum(overlaps),
            self._outside_area(bounds, canvas),
        )

    def _stop_label_placement(
        self,
        stop_name: str,
        _position: Point,
    ) -> tuple[float, float, str]:
        return self._stop_label_placements[stop_name]
