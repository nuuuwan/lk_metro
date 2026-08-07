from .ParallelGeographicDiagramLabelStationCandidatesMixin import \
    ParallelGeographicDiagramLabelStationCandidatesMixin
from .ParallelGeographicDiagramLabelStationPlacementMixin import \
    ParallelGeographicDiagramLabelStationPlacementMixin


class ParallelGeographicDiagramLabelStationMixin(
    ParallelGeographicDiagramLabelStationPlacementMixin,
    ParallelGeographicDiagramLabelStationCandidatesMixin,
):
    pass
