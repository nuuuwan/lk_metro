import math

from lk_metro.GD.Point import Point
from lk_metro.Render.Types import Bounds

Tick = tuple[Point, Point]
TickLabelCandidate = tuple[Tick, Bounds, tuple[float, float, str]]


class HBDTickOrientationMixin:
    def _orient_station_ticks(
        self,
        ticks: dict[str, Tick],
        positions: dict[str, Point],
    ) -> dict[str, Tick]:
        occupied: list[Bounds] = []
        self._place_interchange_labels(positions, occupied)
        oriented = self._select_tick_label_candidates(
            ticks, positions, occupied
        )
        self._station_ticks = oriented
        self._finalize_stop_labels(occupied)
        return oriented

    def _place_interchange_labels(
        self,
        positions: dict[str, Point],
        occupied: list[Bounds],
    ) -> None:
        pending = {
            stop_name
            for stop_name, route_ids in self._label_memberships.items()
            if len(route_ids) > 1
        }
        prefer_positive = True
        while pending:
            candidates = {
                stop_name: self._stop_label_candidates(
                    stop_name,
                    positions,
                    self._label_segments,
                    self._label_memberships,
                    occupied,
                    prefer_positive,
                )
                for stop_name in pending
            }
            stop_name = self._next_tick_label_name(
                pending,
                {name: scores for name, (_, scores) in candidates.items()},
            )
            options, scores = candidates[stop_name]
            selected = options[
                min(
                    range(len(options)),
                    key=lambda index: (
                        scores[index],
                        math.dist(positions[stop_name], options[index][1]),
                    ),
                )
            ]
            self._stop_label_bounds_by_name[stop_name] = selected[0]
            self._stop_label_placements[stop_name] = (*selected[1], "middle")
            occupied.append(selected[0])
            pending.remove(stop_name)
            prefer_positive = not prefer_positive

    def _select_tick_label_candidates(
        self,
        ticks: dict[str, Tick],
        positions: dict[str, Point],
        occupied: list[Bounds],
    ) -> dict[str, Tick]:
        oriented = {}
        pending = set(ticks)
        prefer_positive = True
        while pending:
            candidates = {
                stop_name: self._tick_label_candidates(
                    stop_name,
                    ticks[stop_name],
                    positions[stop_name],
                    prefer_positive,
                )
                for stop_name in pending
            }
            scores = {
                stop_name: [
                    self._tick_label_candidate_score(candidate, occupied)
                    for candidate in stop_candidates
                ]
                for stop_name, stop_candidates in candidates.items()
            }
            stop_name = self._next_tick_label_name(pending, scores)
            selected_index = min(
                range(len(candidates[stop_name])),
                key=scores[stop_name].__getitem__,
            )
            selected = candidates[stop_name][selected_index]
            oriented[stop_name] = selected[0]
            self._stop_label_bounds_by_name[stop_name] = selected[1]
            self._stop_label_placements[stop_name] = selected[2]
            occupied.append(selected[1])
            pending.remove(stop_name)
            prefer_positive = not prefer_positive
        return oriented

    def _next_tick_label_name(
        self,
        pending: set[str],
        scores: dict[str, list[tuple[int, int, int, float, float]]],
    ) -> str:
        return min(
            pending,
            key=lambda name: self._label_priority(
                name,
                self._label_memberships,
                sum(not any(score) for score in scores[name]),
            ),
        )

    def _tick_label_candidates(
        self,
        stop_name: str,
        tick: Tick,
        position: Point,
        prefer_positive: bool,
    ) -> list[TickLabelCandidate]:
        x_delta = tick[1][0] - position[0]
        y_delta = tick[1][1] - position[1]
        length = math.hypot(x_delta, y_delta)
        direction = (x_delta / length, y_delta / length)
        directions = (direction, (-direction[0], -direction[1]))
        if not prefer_positive:
            directions = tuple(reversed(directions))
        return [
            self._tick_label_candidate(
                stop_name, position, candidate_direction
            )
            for candidate_direction in directions
        ]

    def _tick_label_candidate(
        self,
        stop_name: str,
        position: Point,
        direction: Point,
    ) -> TickLabelCandidate:
        inner = (
            position[0] + direction[0] * self.ROUTE_STROKE_WIDTH / 2,
            position[1] + direction[1] * self.ROUTE_STROKE_WIDTH / 2,
        )
        tick = inner, (
            inner[0] + direction[0] * self.STATION_TICK_LENGTH,
            inner[1] + direction[1] * self.STATION_TICK_LENGTH,
        )
        font_size = self._label_font_size(stop_name)
        half_width = self._label_width(stop_name, font_size) / 2
        half_height = self._label_half_height(stop_name, font_size)
        label_radius = self._label_radius(direction, half_width, half_height)
        label_distance = self.LABEL_HALO_WIDTH + label_radius
        label_position = (
            tick[1][0] + direction[0] * label_distance,
            tick[1][1] + direction[1] * label_distance,
        )
        placement = (*label_position, "middle")
        bounds = (
            label_position[0] - half_width,
            label_position[1] - half_height,
            label_position[0] + half_width,
            label_position[1] + half_height,
        )
        return tick, bounds, placement

    def _tick_label_candidate_score(
        self,
        candidate: TickLabelCandidate,
        occupied: list[Bounds],
    ) -> tuple[int, int, int, float, float]:
        placement = candidate[2]
        option = (candidate[1], (placement[0], placement[1]))
        return self._label_option_score(
            option,
            occupied,
            self._label_segments,
        )

    def _tick_to_label(
        self,
        tick: tuple[Point, Point],
        position: Point,
        label_position: Point,
        label_bounds: Bounds,
    ) -> tuple[Point, Point]:
        label_edge = self._label_edge(position, label_position, label_bounds)
        opposite = position
        if position not in tick:
            label_vector = (
                label_edge[0] - position[0],
                label_edge[1] - position[1],
            )
            vector_length = self._point_length(label_vector)
            opposite_length = self.STATION_TICK_LENGTH - vector_length
            opposite = (
                position[0]
                - label_vector[0] / vector_length * opposite_length,
                position[1]
                - label_vector[1] / vector_length * opposite_length,
            )
        return opposite, label_edge

    @staticmethod
    def _point_length(point: Point) -> float:
        return (point[0] ** 2 + point[1] ** 2) ** 0.5

    @staticmethod
    def _label_edge(
        position: Point,
        label_position: Point,
        bounds: Bounds,
    ) -> Point:
        x_delta = label_position[0] - position[0]
        y_delta = label_position[1] - position[1]
        fractions = []
        if x_delta:
            fractions.append(
                min(
                    (bounds[0] - position[0]) / x_delta,
                    (bounds[2] - position[0]) / x_delta,
                )
            )
        if y_delta:
            fractions.append(
                min(
                    (bounds[1] - position[1]) / y_delta,
                    (bounds[3] - position[1]) / y_delta,
                )
            )
        fraction = max(fractions)
        return (
            position[0] + fraction * x_delta,
            position[1] + fraction * y_delta,
        )
