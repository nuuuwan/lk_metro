from ..ParallelGeographicDiagram import ParallelGeographicDiagram
from .HarryBeckDiagramDesignProjectionMixin import \
    HarryBeckDiagramDesignProjectionMixin
from .HarryBeckDiagramGeometryRoutesMixin import \
    HarryBeckDiagramGeometryRoutesMixin
from .HarryBeckDiagramInitMixin import HarryBeckDiagramInitMixin
from .HarryBeckDiagramLegendLayoutMixin import \
    HarryBeckDiagramLegendLayoutMixin
from .HarryBeckDiagramProjectionOpsMixin import \
    HarryBeckDiagramProjectionOpsMixin
from .HarryBeckDiagramSegmentIntersectionMixin import \
    HarryBeckDiagramSegmentIntersectionMixin
from .HarryBeckDiagramStyleMixin import HarryBeckDiagramStyleMixin
from .HarryBeckDiagramSvgMixin import HarryBeckDiagramSvgMixin


class HarryBeckDiagram(
    HarryBeckDiagramStyleMixin,
    HarryBeckDiagramInitMixin,
    HarryBeckDiagramSvgMixin,
    HarryBeckDiagramLegendLayoutMixin,
    HarryBeckDiagramGeometryRoutesMixin,
    HarryBeckDiagramSegmentIntersectionMixin,
    HarryBeckDiagramDesignProjectionMixin,
    HarryBeckDiagramProjectionOpsMixin,
    ParallelGeographicDiagram,
):
    pass
