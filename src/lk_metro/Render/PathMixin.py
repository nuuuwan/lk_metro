from lk_metro.GD.Point import Point


class PathMixin:
    def _route_path_data(self, segments: list[list[Point]]) -> str:
        first = segments[0][0]
        commands = [f"M {first[0]},{first[1]}"]
        previous = first
        for segment in segments:
            for point in segment:
                if point != previous:
                    commands.append(f"L {point[0]},{point[1]}")
                    previous = point
        return " ".join(commands)
