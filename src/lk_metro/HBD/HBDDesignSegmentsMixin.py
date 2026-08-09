import math
import re

from utils_future import Log

log = Log("HBD")


class HBDDesignSegmentsMixin:
    @staticmethod
    def _parse_fitted_shape(
        route_id: str,
        sequence: object,
    ) -> tuple[object, tuple[float, float] | None, bool]:
        if not isinstance(sequence, str):
            return sequence, None, False
        number = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
        ellipse_match = re.fullmatch(
            rf"(.*)/Ellipse\(\s*({number})\s*,\s*({number})\s*\)",
            sequence,
        )
        circle_match = re.fullmatch(
            rf"(.*)/Circle(?:\(\s*({number})\s*\))?",
            sequence,
        )
        if ellipse_match is not None:
            sequence = ellipse_match.group(1)
            radii = tuple(map(float, ellipse_match.groups()[1:]))
        elif circle_match is not None:
            sequence = circle_match.group(1)
            radius = (
                float(circle_match.group(2))
                if circle_match.group(2) is not None
                else None
            )
            radii = (radius, radius) if radius is not None else None
        else:
            return sequence, None, False
        if radii is not None and any(
            not math.isfinite(radius) or radius <= 0 for radius in radii
        ):
            raise ValueError(
                f"Harry Beck route {route_id} fitted radii must be positive"
            )
        return sequence, radii, True

    @staticmethod
    def _parse_circle(
        route_id: str,
        sequence: object,
    ) -> tuple[float, float, float, bool] | None:
        if not isinstance(sequence, str):
            return None
        number = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
        circle_match = re.fullmatch(
            rf"circle\(\s*({number})\s*,\s*({number})"
            rf"(?:\s*,\s*(True|False))?\s*\)",
            sequence,
        )
        ellipse_match = re.fullmatch(
            rf"ellipse\(\s*({number})\s*,\s*({number})\s*,\s*({number})"
            rf"(?:\s*,\s*(True|False))?\s*\)",
            sequence,
        )
        if ellipse_match is not None:
            start_degrees, x_radius, y_radius = map(
                float, ellipse_match.groups()[:3]
            )
            result = HBDDesignSegmentsMixin._validated_ellipse(
                route_id,
                start_degrees,
                x_radius,
                y_radius,
                ellipse_match.group(4) == "True",
            )
        elif circle_match is not None:
            start_degrees, radius = map(float, circle_match.groups()[:2])
            result = HBDDesignSegmentsMixin._validated_ellipse(
                route_id,
                start_degrees,
                radius,
                radius,
                circle_match.group(3) == "True",
            )
        else:
            result = None
        return result

    @staticmethod
    def _validated_ellipse(
        route_id: str,
        start_degrees: float,
        x_radius: float,
        y_radius: float,
        is_clockwise: bool,
    ) -> tuple[float, float, float, bool]:
        if not all(
            math.isfinite(value)
            for value in (start_degrees, x_radius, y_radius)
        ):
            raise ValueError(
                f"Harry Beck route {route_id} has invalid ellipse"
            )
        if x_radius <= 0 or y_radius <= 0:
            raise ValueError(
                f"Harry Beck route {route_id} ellipse radii must be positive"
            )
        return start_degrees % 360, x_radius, y_radius, is_clockwise

    @staticmethod
    def _segments_from_circle(
        designed_stops: list[str],
    ) -> list[dict[str, object]]:
        return [
            {
                "circle": True,
                "circle_index": index,
                "stops": [first, second],
            }
            for index, (first, second) in enumerate(
                zip(designed_stops, designed_stops[1:])
            )
        ]

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
            log.warn(
                "Harry Beck design must contain at least one valid route"
            )
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
