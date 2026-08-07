from lk_metro.ParallelGeographicDiagram.\
    ParallelGeographicDiagramLabelBoundsMixin import (
        ParallelGeographicDiagramLabelBoundsMixin,
    )
from lk_metro.ParallelGeographicDiagram.\
    ParallelGeographicDiagramLabelRefineFlowMixin import (
        ParallelGeographicDiagramLabelRefineFlowMixin,
    )


class ParallelGeographicDiagramLabelRefineMixin(
    ParallelGeographicDiagramLabelRefineFlowMixin,
    ParallelGeographicDiagramLabelBoundsMixin,
):
    pass
