import math

from lk_metro.GD.Point import Point


class PGDRouteGeometryMixin:
    @staticmethod
    def _octilinear_path(first: Point, second: Point) -> list[Point]:
        x_delta = second[0] - first[0]
        y_delta = second[1] - first[1]
        if (
            math.isclose(x_delta, 0.0, abs_tol=1e-9)
            or math.isclose(y_delta, 0.0, abs_tol=1e-9)
            or math.isclose(abs(x_delta), abs(y_delta), abs_tol=1e-9)
        ):
            midpoint = (
                (first[0] + second[0]) / 2,
                (first[1] + second[1]) / 2,
            )
            return [first, midpoint, second]
        if abs(x_delta) > abs(y_delta):
            bend = (
                first[0] + math.copysign(abs(y_delta), x_delta),
                second[1],
            )
        else:
            bend = (
                second[0],
                first[1] + math.copysign(abs(x_delta), y_delta),
            )
        return [first, bend, second]

    @staticmethod
    def _offset_path(path: list[Point], offset: float) -> list[Point]:
        if math.isclose(offset, 0.0):
            return path
        if all(first == second for first, second in zip(path, path[1:])):
            return path
        normals = PGDRouteGeometryMixin._path_normals(path)
        offset_points = [
            (
                path[0][0] + normals[0][0] * offset,
                path[0][1] + normals[0][1] * offset,
            )
        ]
        for point, first_normal, second_normal in zip(
            path[1:-1], normals, normals[1:]
        ):
            miter = (
                first_normal[0] + second_normal[0],
                first_normal[1] + second_normal[1],
            )
            miter_scale = offset / (
                miter[0] * first_normal[0] + miter[1] * first_normal[1]
            )
            offset_points.append(
                (
                    point[0] + miter[0] * miter_scale,
                    point[1] + miter[1] * miter_scale,
                )
            )
        offset_points.append(
            (
                path[-1][0] + normals[-1][0] * offset,
                path[-1][1] + normals[-1][1] * offset,
            )
        )
        return offset_points

    @staticmethod
    def _path_normals(path: list[Point]) -> list[Point]:
        normals = []
        for first, second in zip(path, path[1:]):
            x_delta = second[0] - first[0]
            y_delta = second[1] - first[1]
            length = math.hypot(x_delta, y_delta)
            normals.append((-y_delta / length, x_delta / length))
        return normals
