from lk_metro.GD.Point import Point


class PathMixin:
    def _route_path_data(self, segments: list[list[Point]]) -> str:
        commands = []
        for segment in segments:
            first, *following = segment
            commands.append(f"M {first[0]},{first[1]}")
            commands.extend(f"L {point[0]},{point[1]}" for point in following)
        return " ".join(commands)
