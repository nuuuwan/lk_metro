from collections import defaultdict


class HBDGeometryOverlapCrossingMixin:
    def _overlap_errors(self, positions: dict[str, list[float]]) -> list[str]:
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
                    f"stops {formatted} overlap at "
                    f"({position[0]:g}, {position[1]:g})"
                )
        return errors

    def _crossing_errors(
        self,
        positions: dict[str, list[float]],
        edges: list[tuple[str, str, str]],
    ) -> list[str]:
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
                first_start_label = self._format_stop_at(
                    first_start,
                    positions[first_start],
                )
                first_end_label = self._format_stop_at(
                    first_end, positions[first_end]
                )
                second_start_label = self._format_stop_at(
                    second_start,
                    positions[second_start],
                )
                second_end_label = self._format_stop_at(
                    second_end,
                    positions[second_end],
                )
                errors.append(
                    f"route {first_route} edge {first_start_label} "
                    f"to {first_end_label} crosses route {second_route} edge "
                    f"{second_start_label} to {second_end_label} "
                    f"at ({point[0]:g}, {point[1]:g}) without a shared stop"
                )
        return errors
