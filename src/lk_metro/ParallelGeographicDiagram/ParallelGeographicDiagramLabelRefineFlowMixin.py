from ._PlacementContext import _PlacementContext
from ._StationPlacement import _StationPlacement
from .ParallelGeographicDiagramTypes import Bounds, LabelOption


class ParallelGeographicDiagramLabelRefineFlowMixin:
    def _refine_station_labels(
        self,
        context: _PlacementContext,
        state: _StationPlacement,
    ) -> None:
        label_names = list(state.label_options)
        for pass_index in range(4):
            ordered_names = (
                label_names if pass_index % 2 == 0 else reversed(label_names)
            )
            for stop_name in ordered_names:
                state.selected_indices[stop_name] = self._best_refined_option(
                    stop_name,
                    label_names,
                    context,
                    state,
                )
        context.placed_labels = context.placed_labels[
            : len(context.fixed_bounds)
        ]
        for stop_name, options in state.label_options.items():
            selected = options[state.selected_indices[stop_name]]
            self._apply_station_option(
                stop_name, selected, context, state, False
            )

    def _best_refined_option(
        self,
        stop_name: str,
        label_names: list[str],
        context: _PlacementContext,
        state: _StationPlacement,
    ) -> int:
        route_id = next(iter(context.memberships[stop_name]))
        other_bounds = [
            state.label_options[name][state.selected_indices[name]][0]
            for name in label_names
            if name != stop_name
        ]
        scores = [
            self._refined_option_score(
                option, route_id, other_bounds, context, state
            )
            for option in state.label_options[stop_name]
        ]
        return min(range(len(scores)), key=scores.__getitem__)

    def _refined_option_score(
        self,
        option: LabelOption,
        route_id: str,
        other_bounds: list[Bounds],
        context: _PlacementContext,
        state: _StationPlacement,
    ) -> tuple[float, float, float, float, int, float]:
        bounds, payload = option
        side = "above" if payload[2][1] < 0 else "below"
        return (
            self._outside_area(bounds, context.canvas_bounds),
            sum(
                self._overlap_area(bounds, item)
                for item in context.fixed_bounds
            ),
            sum(self._overlap_area(bounds, item) for item in other_bounds),
            payload[3],
            state.side_counts[route_id][side],
            sum(
                self._overlap_area(bounds, route)
                for route in context.route_bounds
            ),
        )
