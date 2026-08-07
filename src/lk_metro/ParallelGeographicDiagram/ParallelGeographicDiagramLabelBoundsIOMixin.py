from pathlib import Path

from utils_future import Log

from lk_metro.ParallelGeographicDiagram.\
    ParallelGeographicDiagramTypes import (
        Bounds,
    )

log = Log("ParallelGeographicDiagram")


class ParallelGeographicDiagramLabelBoundsIOMixin:
    def _warn_label_overlaps(
        self,
        placed_labels: list[tuple[str, Bounds]],
    ) -> None:
        for index, (first_name, first_bounds) in enumerate(placed_labels):
            for second_name, second_bounds in placed_labels[index + 1:]:
                overlap = self._overlap_area(first_bounds, second_bounds)
                if overlap > 0.01:
                    log.warn(
                        "Label overlap: "
                        f"{first_name!r} overlaps {second_name!r} "
                        f"by {overlap:.2f} square units"
                    )

    def write_svg(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.write_text(self.to_svg(), encoding="utf-8")
        return output_path
