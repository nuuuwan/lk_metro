import math

from lk_metro.GD.Point import Point
from lk_metro.Render.Types import Bounds


class LabelBoundsGeometryMixin:
    def _label_bounds(
        self,
        anchor: Point,
        label: str,
        outward: Point,
        font_size: float,
    ) -> tuple[float, float, float, float]:
        label_lines = self._label_lines(label)
        text_width = max(
            font_size, max(map(len, label_lines)) * font_size * 0.52
        )
        half_height = self._label_half_height(label, font_size)
        if not self.ROTATE_LABELS:
            if outward[0] < 0:
                return (
                    anchor[0] - text_width,
                    anchor[1] - half_height,
                    anchor[0],
                    anchor[1] + half_height,
                )
            return (
                anchor[0],
                anchor[1] - half_height,
                anchor[0] + text_width,
                anchor[1] + half_height,
            )
        return self._rotated_label_bounds(
            anchor, outward, text_width, half_height
        )

    def _rotated_label_bounds(
        self,
        anchor: Point,
        outward: Point,
        text_width: float,
        half_height: float,
    ) -> Bounds:
        length = math.hypot(*outward)
        x_direction = outward[0] / length
        y_direction = outward[1] / length
        x_normal = -y_direction
        y_normal = x_direction
        corners = [
            (
                anchor[0] + x_direction * distance + x_normal * offset,
                anchor[1] + y_direction * distance + y_normal * offset,
            )
            for distance in (0.0, text_width)
            for offset in (-half_height, half_height)
        ]
        return (
            min(point[0] for point in corners),
            min(point[1] for point in corners),
            max(point[0] for point in corners),
            max(point[1] for point in corners),
        )

    def _label_half_height(self, label: str, font_size: float) -> float:
        line_count = len(self._label_lines(label))
        return font_size * (0.6 + (line_count - 1) * 1.05 / 2)

    @staticmethod
    def _overlap_area(first: Bounds, second: Bounds) -> float:
        width = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
        height = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
        return width * height

    @classmethod
    def _outside_area(cls, bounds: Bounds, container: Bounds) -> float:
        area = max(0.0, bounds[2] - bounds[0]) * max(
            0.0, bounds[3] - bounds[1]
        )
        return area - cls._overlap_area(bounds, container)
