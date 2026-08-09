import math

from lk_metro.GD.Point import Point
from lk_metro.HBD.HBDLabelCandidateGeometryMixin import \
    HBDLabelCandidateGeometryMixin
from lk_metro.Render.Types import Bounds
from lk_metro.Route import Route

LabelOption = tuple[Bounds, Point]


class HBDLabelCandidatesMixin(HBDLabelCandidateGeometryMixin):
    def _side_label_options(
        self,
        stop_name: str,
        position: Point,
        segments: dict[str, list[list[Point]]],
        route_ids: set[str],
        prefer_positive: bool,
    ) -> list[LabelOption]:
        font_size = self._label_font_size(stop_name)
        label = stop_name
        half_width = self._label_width(label, font_size) / 2
        half_height = self._label_half_height(label, font_size)
        routes_by_id = {route.id: route for route in self.routes}
        options = []
        for route_id in sorted(route_ids):
            normal = self._route_normal(
                stop_name, routes_by_id[route_id], segments[route_id]
            )
            for direction in self._label_directions(normal, prefer_positive):
                edge_distances = self._label_edge_distances(
                    stop_name, route_ids
                )
                if len(route_ids) > 1:
                    distance = self._interchange_label_edge_distance(
                        stop_name, position, direction
                    )
                    edge_distances = tuple(
                        distance + index * self.LABEL_FONT_SIZE / 2
                        for index in range(8)
                    )
                radius = self._label_radius(
                    direction, half_width, half_height
                )
                for edge_distance in edge_distances:
                    clearance = edge_distance + radius
                    center = (
                        position[0] + direction[0] * clearance,
                        position[1] + direction[1] * clearance,
                    )
                    bounds = (
                        center[0] - half_width,
                        center[1] - half_height,
                        center[0] + half_width,
                        center[1] + half_height,
                    )
                    options.append((bounds, center))
        return options

    def _interchange_label_edge_distance(
        self,
        stop_name: str,
        position: Point,
        direction: Point,
    ) -> float:
        points = self._interchange_route_points(stop_name)
        first, second, inner_width = self._interchange_capsule_geometry(
            points
        )
        capsule_radius = inner_width / 2 + self.INTERCHANGE_STROKE_WIDTH
        return (
            max(
                (point[0] - position[0]) * direction[0]
                + (point[1] - position[1]) * direction[1]
                for point in (first, second)
            )
            + capsule_radius
            + self.LABEL_HALO_WIDTH
        )

    def _route_normal(
        self,
        stop_name: str,
        route: Route,
        route_segments: list[list[Point]],
    ) -> Point:
        stop_index = route.stops.index(stop_name)
        candidates = self._tick_candidate_segments(route_segments, stop_index)
        first, second = next(
            pair
            for pair in candidates
            if not math.isclose(math.dist(*pair), 0)
        )
        x_delta = second[0] - first[0]
        y_delta = second[1] - first[1]
        length = math.hypot(x_delta, y_delta)
        return -y_delta / length, x_delta / length

    def _label_width(self, label: str, font_size: float) -> float:
        return max(
            font_size,
            max(map(len, self._label_lines(label))) * font_size * 0.52,
        )
