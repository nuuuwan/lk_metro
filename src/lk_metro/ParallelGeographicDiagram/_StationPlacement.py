from dataclasses import dataclass

from lk_metro.ParallelGeographicDiagram.ParallelGeographicDiagramTypes import (
    LabelOption, Tick)


@dataclass
class _StationPlacement:
    selected_ticks: dict[str, Tick]
    label_options: dict[str, list[LabelOption]]
    selected_indices: dict[str, int]
    side_counts: dict[str, dict[str, int]]
