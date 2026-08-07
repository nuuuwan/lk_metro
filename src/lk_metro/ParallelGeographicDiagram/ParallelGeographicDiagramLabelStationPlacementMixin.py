from lk_metro.GeographicDiagram.Point import Point
from lk_metro.ParallelGeographicDiagram._PlacementContext import \
    _PlacementContext
from lk_metro.ParallelGeographicDiagram._StationPlacement import \
    _StationPlacement
from lk_metro.ParallelGeographicDiagram.ParallelGeographicDiagramTypes import (
    LabelOption, Tick)


class ParallelGeographicDiagramLabelStationPlacementMixin:
    def _place_station_labels(
        self,
        context: _PlacementContext,
        ticks: dict[str, Tick],
    ) -> _StationPlacement:
        state = _StationPlacement(
            selected_ticks={},
            label_options={},
            selected_indices={},
            side_counts={
                route.id: {"above": 0, "below": 0} for route in self.routes
            },
        )
        stop_names = sorted(
            ticks,
            key=lambda name: (
                -max(map(len, self._label_lines(self._stop_label(name)))),
                context.positions[name][1],
                context.positions[name][0],
            ),
        )
        for stop_name in stop_names:
            self._place_station_label(
                stop_name, ticks[stop_name], context, state
            )
        return state

    def _place_station_label(
        self,
        stop_name: str,
        tick: Tick,
        context: _PlacementContext,
        state: _StationPlacement,
    ) -> None:
        options = self._station_label_options(
            stop_name, tick, context.positions[stop_name]
        )
        route_id = next(iter(context.memberships[stop_name]))
        scores = [
            self._station_option_score(option, route_id, context, state)
            for option in options
        ]
        selected_index = min(range(len(options)), key=scores.__getitem__)
        state.label_options[stop_name] = options
        state.selected_indices[stop_name] = selected_index
        selected = options[selected_index]
        if not self.ROTATE_LABELS:
            side = "above" if selected[1][2][1] < 0 else "below"
            state.side_counts[route_id][side] += 1
        self._apply_station_option(stop_name, selected, context, state, True)

    def _station_label_options(
        self,
        stop_name: str,
        tick: Tick,
        position: Point,
    ) -> list[LabelOption]:
        font_size = self._label_font_size(stop_name)
        clearance = self._label_half_height(
            self._stop_label(stop_name), font_size
        )
        clearance += 0.2
        if self.ROTATE_LABELS:
            payloads = self._rotated_candidate_payloads(
                tick, position, clearance
            )
        else:
            payloads = self._horizontal_candidate_payloads(
                tick, font_size, clearance
            )
        return [
            (
                self._label_bounds(
                    payload[1],
                    self._stop_label(stop_name),
                    payload[2],
                    font_size,
                ),
                payload,
            )
            for payload in payloads
        ]
