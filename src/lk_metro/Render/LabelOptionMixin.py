from lk_metro.Render._PlacementContext import _PlacementContext
from lk_metro.Render._StationPlacement import _StationPlacement
from lk_metro.Render.Types import LabelOption


class LabelOptionMixin:
    def _station_option_score(
        self,
        option: LabelOption,
        route_id: str,
        context: _PlacementContext,
        state: _StationPlacement,
    ) -> tuple[float, float, float, float, int, float]:
        bounds, payload = option
        side = "above" if payload[2][1] < 0 else "below"
        side_count = (
            0 if self.ROTATE_LABELS else state.side_counts[route_id][side]
        )
        return (
            self._outside_area(bounds, context.canvas_bounds),
            sum(
                self._overlap_area(bounds, item)
                for item in context.fixed_bounds
            ),
            sum(
                self._overlap_area(bounds, item)
                for item in context.occupied[len(context.fixed_bounds):]
            ),
            payload[3],
            side_count,
            sum(
                self._overlap_area(bounds, route)
                for route in context.route_bounds
            ),
        )

    def _apply_station_option(
        self,
        stop_name: str,
        option: LabelOption,
        context: _PlacementContext,
        state: _StationPlacement,
        add_to_occupied: bool,
    ) -> None:
        bounds, payload = option
        selected_tick, label_position, outward, _ = payload
        state.selected_ticks[stop_name] = selected_tick
        self._station_label_positions[stop_name] = label_position
        self._station_label_text_anchors[stop_name] = (
            "end" if outward[0] < 0 else "start"
        )
        if add_to_occupied:
            context.occupied.append(bounds)
        context.placed_labels.append((stop_name, bounds))
