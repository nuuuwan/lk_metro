from .ParallelGeographicDiagramTickGeometryMixin import \
    ParallelGeographicDiagramTickGeometryMixin
from .ParallelGeographicDiagramTickPlacementMixin import \
    ParallelGeographicDiagramTickPlacementMixin


class ParallelGeographicDiagramTickMixin(
    ParallelGeographicDiagramTickPlacementMixin,
    ParallelGeographicDiagramTickGeometryMixin,
):
    pass
