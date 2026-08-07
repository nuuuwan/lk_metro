from .ParallelGeographicDiagramLabelBoundsMixin import \
    ParallelGeographicDiagramLabelBoundsMixin
from .ParallelGeographicDiagramLabelRefineFlowMixin import \
    ParallelGeographicDiagramLabelRefineFlowMixin


class ParallelGeographicDiagramLabelRefineMixin(
    ParallelGeographicDiagramLabelRefineFlowMixin,
    ParallelGeographicDiagramLabelBoundsMixin,
):
    pass
