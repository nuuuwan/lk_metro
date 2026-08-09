from collections import defaultdict

from lk_metro.HBD.HBDGeometryEdgeValidationMixin import GeometryWarning


class HBDGeometryOverlapCrossingMixin:
    def _overlap_errors(
        self, positions: dict[str, list[float]]
    ) -> list[GeometryWarning]:
        errors = []
        stops_by_position = defaultdict(list)
        for stop_name, position in positions.items():
            stops_by_position[tuple(position)].append(stop_name)
        for position, stop_names in stops_by_position.items():
            if len(stop_names) > 1:
                labels = sorted(stop_names)
                formatted = ", ".join(
                    self._format_stop_at(name, positions[name])
                    for name in labels
                )
                errors.append(
                    (
                        "stop overlap",
                        tuple(labels),
                        f"{formatted} overlap at "
                        f"({position[0]:g}, {position[1]:g})",
                    )
                )
        return errors

    def _crossing_errors(
        self,
        positions: dict[str, list[float]],
        edges: list[tuple[str, str, str]],
    ) -> list[GeometryWarning]:
        errors = []
        for index, (first_route, first_start, first_end) in enumerate(edges):
            for second_route, second_start, second_end in edges[index + 1:]:
                if {first_start, first_end} & {second_start, second_end}:
                    continue
                point = self._proper_segment_intersection(
                    positions[first_start],
                    positions[first_end],
                    positions[second_start],
                    positions[second_end],
                )
                if point is None:
                    continue
                errors.append(
                    self._crossing_warning(
                        first_route,
                        first_start,
                        first_end,
                        second_route,
                        second_start,
                        second_end,
                        point,
                        positions,
                    )
                )
        return errors

    def _crossing_warning(
        self,
        first_route: str,
        first_start: str,
        first_end: str,
        second_route: str,
        second_start: str,
        second_end: str,
        point: tuple[float, float],
        positions: dict[str, list[float]],
    ) -> GeometryWarning:
        labels = {
            stop: self._format_stop_at(stop, positions[stop])
            for stop in (first_start, first_end, second_start, second_end)
        }
        return (
            "route crossing",
            (first_start, first_end, second_start, second_end),
            f"route {first_route} edge {labels[first_start]} to "
            f"{labels[first_end]} crosses route {second_route} edge "
            f"{labels[second_start]} to {labels[second_end]} at "
            f"({point[0]:g}, {point[1]:g}) without a shared stop",
        )
