from lk_metro.GeographicDiagram.Point import Point
from lk_metro.HarryBeckDiagram.HarryBeckDiagramLabelCandidatesMixin import \
    HarryBeckDiagramLabelCandidatesMixin
from lk_metro.ParallelGeographicDiagram.ParallelGeographicDiagramTypes import \
    Bounds


class HarryBeckDiagramLabelPlacementMixin(
    HarryBeckDiagramLabelCandidatesMixin,
):
    def _prepare_stop_labels(self, positions: dict[str, Point]) -> None:
        options = {
            stop.name: self._corner_label_options(
                stop.name, positions[stop.name]
            )
            for stop in self.stops
        }
        names = sorted(
            options,
            key=lambda name: self._bounds_area(options[name][0][0]),
            reverse=True,
        )
        fixed_bounds = [bounds for _, bounds in self._route_name_bounds()]
        selected = {}
        for name in names:
            selected[name] = self._best_corner_index(
                name, options, selected, fixed_bounds
            )
        self._refine_corner_selection(names, options, selected, fixed_bounds)
        self._stop_label_placements = {
            name: (*options[name][index][1], options[name][index][2])
            for name, index in selected.items()
        }

    def _stop_label_placement(
        self,
        stop_name: str,
        position: Point,
    ) -> tuple[float, float, str]:
        return self._stop_label_placements[stop_name]

    def _refine_corner_selection(
        self,
        names: list[str],
        options: dict[str, list[tuple[Bounds, Point, str]]],
        selected: dict[str, int],
        fixed_bounds: list[Bounds],
    ) -> None:
        changed = True
        while changed:
            changed = False
            for name in names:
                best_index = self._best_corner_index(
                    name, options, selected, fixed_bounds
                )
                changed |= best_index != selected[name]
                selected[name] = best_index

    def _best_corner_index(
        self,
        stop_name: str,
        options: dict[str, list[tuple[Bounds, Point, str]]],
        selected: dict[str, int],
        fixed_bounds: list[Bounds],
    ) -> int:
        occupied = fixed_bounds + [
            options[name][selected[name]][0]
            for name in sorted(selected)
            if name != stop_name
        ]
        scores = [
            (
                sum(self._overlap_area(option[0], item) for item in occupied),
                self._outside_area(
                    option[0],
                    (0.0, 0.0, float(self.width), float(self.height)),
                ),
                index,
            )
            for index, option in enumerate(options[stop_name])
        ]
        return min(range(len(scores)), key=scores.__getitem__)

    @staticmethod
    def _bounds_area(bounds: Bounds) -> float:
        return (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
