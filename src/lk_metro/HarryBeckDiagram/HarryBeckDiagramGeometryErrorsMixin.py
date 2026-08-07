from lk_metro.HarryBeckDiagram.\
    HarryBeckDiagramGeometryEdgeValidationMixin import (
        HarryBeckDiagramGeometryEdgeValidationMixin,
    )
from lk_metro.HarryBeckDiagram.\
    HarryBeckDiagramGeometryOverlapCrossingMixin import (
        HarryBeckDiagramGeometryOverlapCrossingMixin,
    )


class HarryBeckDiagramGeometryErrorsMixin(
    HarryBeckDiagramGeometryEdgeValidationMixin,
    HarryBeckDiagramGeometryOverlapCrossingMixin,
):
    pass
