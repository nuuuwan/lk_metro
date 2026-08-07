class HBDProjectionFlowMixin:
    def _project_positions(
        self,
        origin_positions: dict[str, list[float]],
        design_routes: list[dict[str, object]],
    ) -> dict[str, list[float]]:
        pending_segments = self._pending_segments(design_routes)
        projected = {
            name: point[:] for name, point in origin_positions.items()
        }
        position_routes = {name: set() for name in origin_positions}
        while pending_segments:
            remaining = self._project_available_segments(
                pending_segments,
                projected,
                position_routes,
            )
            if len(remaining) == len(pending_segments):
                self._add_fallback_origin(
                    remaining[0], projected, position_routes
                )
            else:
                pending_segments = remaining
        return projected

    def _pending_segments(
        self,
        design_routes: list[dict[str, object]],
    ) -> list[tuple[str, list[str], int, int]]:
        pending = []
        for route in design_routes:
            for segment in route["segments"]:
                direction_index = self.DIRECTIONS.index(segment["direction"])
                x_delta, y_delta = self.DIRECTION_VECTORS[direction_index]
                pending.append(
                    (route["id"], segment["stops"], x_delta, y_delta)
                )
        return pending

    def _project_available_segments(
        self,
        pending_segments: list[tuple[str, list[str], int, int]],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> list[tuple[str, list[str], int, int]]:
        remaining_segments = []
        for segment in pending_segments:
            if not self._project_segment(segment, projected, position_routes):
                remaining_segments.append(segment)
        return remaining_segments

    def _project_segment(
        self,
        segment: tuple[str, list[str], int, int],
        projected: dict[str, list[float]],
        position_routes: dict[str, set[str]],
    ) -> bool:
        route_id, stops, x_delta, y_delta = segment
        anchor_index = next(
            (index for index, stop in enumerate(stops) if stop in projected),
            None,
        )
        if anchor_index is None:
            return False
        anchor_x, anchor_y = projected[stops[anchor_index]]
        for index, stop in enumerate(stops):
            step_count = index - anchor_index
            expected = [
                anchor_x + step_count * x_delta,
                anchor_y + step_count * y_delta,
            ]
            self._record_projected_stop(
                stop,
                expected,
                route_id,
                projected,
                position_routes,
            )
        return True
