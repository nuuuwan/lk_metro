from .ParallelGeographicDiagramLabelInterchangeCandidatesMixin import \
    ParallelGeographicDiagramLabelInterchangeCandidatesMixin
from .ParallelGeographicDiagramLabelInterchangePlacementMixin import \
    ParallelGeographicDiagramLabelInterchangePlacementMixin


class ParallelGeographicDiagramLabelInterchangeMixin(
    ParallelGeographicDiagramLabelInterchangePlacementMixin,
    ParallelGeographicDiagramLabelInterchangeCandidatesMixin,
):
    pass
