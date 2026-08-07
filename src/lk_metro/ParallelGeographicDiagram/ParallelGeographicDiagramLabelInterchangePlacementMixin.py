from ..GeographicDiagram import Point
from ._PlacementContext import _PlacementContext
from .ParallelGeographicDiagramTypes import Bounds


class ParallelGeographicDiagramLabelInterchangePlacementMixin:
    def _avoid_label_overlaps(
        self,
        positions: dict[str, Point],
        ticks: dict[str, tuple[Point, Point]],
        memberships: dict[str, set[str]],
        segments: dict[str, list[list[Point]]],
    ) -> dict[str, tuple[Point, Point]]:
        placed_labels = self._route_name_bounds()
        occupied = [bounds for _, bounds in placed_labels]
        context = _PlacementContext(
            positions=positions,
            memberships=memberships,
            route_bounds=self._route_segment_bounds(segments),
            canvas_bounds=(0.0, 0.0, float(self.width), float(self.height)),
            occupied=occupied,
            placed_labels=placed_labels,
            fixed_bounds=[],
        )
        self._place_interchange_labels(context)
        context.fixed_bounds = list(context.occupied)
        self._station_label_positions = {}
        self._station_label_text_anchors = {}
        state = self._place_station_labels(context, ticks)
        if not self.ROTATE_LABELS:
            self._refine_station_labels(context, state)
        if self.WARN_LABEL_OVERLAPS:
            self._warn_label_overlaps(context.placed_labels)
        return state.selected_ticks

    def _route_segment_bounds(
        self,
        segments: dict[str, list[list[Point]]],
    ) -> list[Bounds]:
        margin = self.ROUTE_STROKE_WIDTH / 2 + 0.15
        return [
            (
                min(first[0], second[0]) - margin,
                min(first[1], second[1]) - margin,
                max(first[0], second[0]) + margin,
                max(first[1], second[1]) + margin,
            )
            for route_segments in segments.values()
            for path in route_segments
            for first, second in zip(path, path[1:])
        ]

    def _place_interchange_labels(self, context: _PlacementContext) -> None:
        self._interchange_label_positions = {}
        stop_names = sorted(
            (
                stop.name
                for stop in self.stops
                if len(context.memberships[stop.name]) > 1
            ),
            key=lambda name: (
                context.positions[name][1],
                context.positions[name][0],
            ),
        )
        for stop_name in stop_names:
            candidates = self._interchange_candidates(
                context.positions[stop_name]
            )
            bounds = [
                self._label_bounds(
                    (candidate[0], candidate[1]),
                    self._stop_label(stop_name),
                    candidate[3],
                    self._label_font_size(stop_name),
                )
                for candidate in candidates
            ]
            scores = [self._label_score(item, context) for item in bounds]
            selected_index = min(
                range(len(candidates)), key=scores.__getitem__
            )
            self._interchange_label_positions[stop_name] = candidates[
                selected_index
            ][:3]
            context.occupied.append(bounds[selected_index])
            context.placed_labels.append((stop_name, bounds[selected_index]))
