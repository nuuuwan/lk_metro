from .HarryBeckDiagramGeometryEdgeValidationMixin import \
    HarryBeckDiagramGeometryEdgeValidationMixin
from .HarryBeckDiagramGeometryOverlapCrossingMixin import \
    HarryBeckDiagramGeometryOverlapCrossingMixin


class HarryBeckDiagramGeometryErrorsMixin(
    HarryBeckDiagramGeometryEdgeValidationMixin,
    HarryBeckDiagramGeometryOverlapCrossingMixin,
):
    pass
