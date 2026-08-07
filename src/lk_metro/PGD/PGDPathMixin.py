import math

from lk_metro.GD.Point import Point
from lk_metro.PGD.PGDTypes import Edge


class PGDPathMixin:
    def _route_path_data(self, segments: list[list[Point]]) -> str:
        points = []
        for segment in segments:
            if points and points[-1] != segment[0]:
                points.append(
                    (
                        (points[-1][0] + segment[0][0]) / 2,
                        (points[-1][1] + segment[0][1]) / 2,
                    )
                )
            for point in segment:
                if not points or point != points[-1]:
                    points.append(point)
        return self._rounded_path_data(points)

    def _rounded_path_data(self, points: list[Point]) -> str:
        commands = [f"M {points[0][0]},{points[0][1]}"]
        for previous, point, following in zip(points, points[1:], points[2:]):
            command = self._rounded_command(previous, point, following)
            commands.extend(command)
        commands.append(f"L {points[-1][0]},{points[-1][1]}")
        return " ".join(commands)

    def _rounded_command(
        self,
        previous: Point,
        point: Point,
        following: Point,
    ) -> list[str]:
        incoming = (previous[0] - point[0], previous[1] - point[1])
        outgoing = (following[0] - point[0], following[1] - point[1])
        incoming_length = math.hypot(*incoming)
        outgoing_length = math.hypot(*outgoing)
        cross_product = incoming[0] * outgoing[1] - incoming[1] * outgoing[0]
        if math.isclose(cross_product, 0.0, abs_tol=1e-9):
            return [f"L {point[0]},{point[1]}"]
        radius = min(
            self.ROUTE_CURVE_RADIUS,
            incoming_length / 2,
            outgoing_length / 2,
        )
        entry = (
            point[0] + incoming[0] / incoming_length * radius,
            point[1] + incoming[1] / incoming_length * radius,
        )
        exit_point = (
            point[0] + outgoing[0] / outgoing_length * radius,
            point[1] + outgoing[1] / outgoing_length * radius,
        )
        return [
            f"L {entry[0]},{entry[1]}",
            f"Q {point[0]},{point[1]} {exit_point[0]},{exit_point[1]}",
        ]

    @staticmethod
    def _edge_key(first: str, second: str) -> Edge:
        return tuple(sorted((first, second)))
