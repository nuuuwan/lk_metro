import re

from utils_future import Log

log = Log("HBD")


class HBDDesignSegmentsMixin:
    @staticmethod
    def _segments_from_directions(
        route_id: str,
        designed_stops: list[str],
        directions: list[tuple[str, bool]],
    ) -> list[dict[str, object]]:
        segments = []
        current_stop = designed_stops[0]
        next_stop_index = 1
        blank_index = 0
        for direction, is_blank in directions:
            if is_blank:
                blank_index += 1
                next_stop = f"__blank__:{route_id}:{blank_index}"
            else:
                next_stop = designed_stops[next_stop_index]
                next_stop_index += 1
            segments.append(
                {"direction": direction, "stops": [current_stop, next_stop]}
            )
            current_stop = next_stop
        return segments

    def _with_design_fallbacks(
        self,
        origin_positions: dict[str, list[float]],
        segments_by_route: dict[str, list[dict[str, object]]],
        designed_stops_by_route: dict[str, list[str]],
    ) -> tuple[
        dict[str, list[float]],
        dict[str, list[dict[str, object]]],
        dict[str, list[str]],
    ]:
        if not segments_by_route:
            log.warn("Harry Beck design must contain at least one valid route")
            fallback_route = self.routes[0]
            designed_stops = fallback_route.stops
            segments_by_route[fallback_route.id] = [
                {"direction": "N", "stops": [first, second]}
                for first, second in zip(designed_stops, designed_stops[1:])
            ]
            designed_stops_by_route[fallback_route.id] = designed_stops
        if not origin_positions:
            fallback_origin = next(iter(designed_stops_by_route.values()))[0]
            log.warn(f"Using {fallback_origin!r} as the origin stop")
            origin_positions[fallback_origin] = [0.0, 0.0]
        return origin_positions, segments_by_route, designed_stops_by_route

    def _parse_directions(
        self,
        route_id: str,
        direction_sequence: object,
        expected_count: int,
    ) -> list[tuple[str, bool]]:
        directions = []
        if not isinstance(direction_sequence, str) or not direction_sequence:
            raise ValueError(
                f"Harry Beck route {route_id} has no direction sequence"
            )
        for token in direction_sequence.split("-"):
            match = re.fullmatch(r"(\d+)?(b)?(E|SE|S|SW|W|NW|N|NE)", token)
            if match is None or int(match.group(1) or 1) == 0:
                raise ValueError(
                    f"Harry Beck route {route_id} has invalid direction "
                    f"{token!r}"
                )
            repeat_count = int(match.group(1) or 1)
            directions.extend(
                [(match.group(3), match.group(2) == "b")] * repeat_count
            )
        direction_count = sum(not is_blank for _, is_blank in directions)
        if direction_count != expected_count:
            raise ValueError(
                f"Harry Beck route {route_id} requires "
                f"{expected_count} directions, "
                f"but the sequence defines {direction_count}"
            )
        return directions
