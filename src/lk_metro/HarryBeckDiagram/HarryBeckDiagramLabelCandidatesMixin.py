from lk_metro.GeographicDiagram.Point import Point
from lk_metro.ParallelGeographicDiagram.ParallelGeographicDiagramTypes import \
    Bounds


class HarryBeckDiagramLabelCandidatesMixin:
    def _corner_label_options(
        self,
        stop_name: str,
        position: Point,
    ) -> list[tuple[Bounds, Point, str]]:
        label = self._stop_label(stop_name)
        font_size = self._label_font_size(stop_name)
        half_height = self._label_half_height(label, font_size)
        options = []
        for text_anchor, x_direction in (("start", 1.0), ("end", -1.0)):
            for y_direction in (1.0, -1.0):
                anchor = (
                    position[0],
                    position[1] + y_direction * half_height,
                )
                bounds = self._label_bounds(
                    anchor,
                    label,
                    (x_direction, 0.0),
                    font_size,
                )
                options.append((bounds, anchor, text_anchor))
        return options
