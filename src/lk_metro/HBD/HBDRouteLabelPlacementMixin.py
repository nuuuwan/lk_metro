from lk_metro.GD.Point import Point
from lk_metro.HBD.HBDRouteLabelCandidatesMixin import \
    HBDRouteLabelCandidatesMixin
from lk_metro.HBD.HBDRouteLabelOptionMixin import RouteLabelOption
from lk_metro.Render.Types import Bounds


class HBDRouteLabelPlacementMixin(HBDRouteLabelCandidatesMixin):
    def _prepare_route_names(
        self,
        segments: dict[str, list[list[Point]]],
    ) -> None:
        occupied = list(self._stop_label_bounds)
        self._route_name_positions = {}
        self._route_name_bounds_by_id = {}
        for route in sorted(self.routes, key=lambda item: item.id):
            route_id = route.id
            options = self._route_label_options(route_id, segments)
            selected = min(
                options,
                key=lambda option, selected_route_id=route_id: (
                    self._route_label_selection_score(
                        selected_route_id, option, occupied
                    )
                ),
            )
            occupied.append(selected[0])
            self._route_name_bounds_by_id[route_id] = selected[0]
            self._route_name_positions[route_id] = (*selected[1], 0.0)

    def _route_label_selection_score(
        self,
        route_id: str,
        option: RouteLabelOption,
        occupied: list[Bounds],
    ) -> tuple[float, ...]:
        score = self._route_label_score(option, occupied)
        target_name = self.ROUTE_LABEL_TARGET_STOPS.get(route_id)
        if target_name is None:
            return score
        target = self._label_positions[target_name]
        distance = (option[1][0] - target[0]) ** 2 + (
            option[1][1] - target[1]
        ) ** 2
        return (*score[:4], distance, *score[4:])

    def _route_label_score(
        self,
        option: RouteLabelOption,
        occupied: list[Bounds],
    ) -> tuple[int, float, int, float, float, float, float]:
        (
            bounds,
            _,
            terminus_distance,
            own_distance,
            other_distance,
            line_hits,
        ) = option
        overlaps = [self._overlap_area(bounds, other) for other in occupied]
        edge = self.LABEL_CANVAS_PADDING
        canvas = (edge, edge, self.width - edge, self.height - edge)
        return (
            sum(area > 0 for area in overlaps),
            sum(overlaps),
            line_hits,
            self._outside_area(bounds, canvas),
            terminus_distance,
            own_distance,
            -other_distance,
        )
