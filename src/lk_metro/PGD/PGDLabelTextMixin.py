import html

from lk_metro.PGD.PGDTypes import Bounds


class PGDLabelTextMixin:
    def _label_svg_line(
        self,
        stop_name: str,
        label_x: float,
        label_y: float,
        text_anchor: str,
    ) -> str:
        label_lines = self._label_lines(self._stop_label(stop_name))
        line_height = self._label_font_size(stop_name) * 1.05
        first_offset = -(len(label_lines) - 1) * line_height / 2
        label_class = (
            "label terminal-label"
            if self._is_terminus(stop_name)
            else "label"
        )
        tspans = "".join(
            f'<tspan x="{label_x}" dy="'
            f'{first_offset if index == 0 else line_height}">'
            f"{html.escape(label_line)}</tspan>"
            for index, label_line in enumerate(label_lines)
        )
        return (
            f'<text class="{label_class}" x="{label_x}" y="{label_y}" '
            f'text-anchor="{text_anchor}">'
            f"{tspans}</text>"
        )

    def _prepare_stop_labels(
        self,
        positions: dict[str, tuple[float, float]],
    ) -> None:
        pass

    def _stop_label_placement(
        self,
        stop_name: str,
        position: tuple[float, float],
    ) -> tuple[float, float, str]:
        return position[0], position[1], "middle"

    def _background_svg_lines(self) -> list[str]:
        return []

    def _route_name_svg_lines(self) -> list[str]:
        return []

    def _route_name_bounds(self) -> list[tuple[str, Bounds]]:
        return []

    def _route_name_font_size(self) -> float:
        return self.LABEL_FONT_SIZE

    def _terminal_label_font_size(self) -> float:
        return self.LABEL_FONT_SIZE

    def _is_terminus(self, stop_name: str) -> bool:
        return any(
            stop_name in (route.stops[0], route.stops[-1])
            for route in self.routes
        )

    def _label_font_size(self, stop_name: str) -> float:
        return (
            self._terminal_label_font_size()
            if self._is_terminus(stop_name)
            else self.LABEL_FONT_SIZE
        )

    def _stop_label(self, stop_name: str) -> str:
        return stop_name

    def _label_lines(self, label: str) -> tuple[str, ...]:
        return tuple(label.split())
