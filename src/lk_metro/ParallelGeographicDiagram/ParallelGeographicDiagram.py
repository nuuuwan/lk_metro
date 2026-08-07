from ..GeographicDiagram import GeographicDiagram
from .ParallelGeographicDiagramCoreMixin import \
    ParallelGeographicDiagramCoreMixin
from .ParallelGeographicDiagramLabelBoundsMixin import \
    ParallelGeographicDiagramLabelBoundsMixin
from .ParallelGeographicDiagramLabelInterchangeCandidatesMixin import \
    ParallelGeographicDiagramLabelInterchangeCandidatesMixin
from .ParallelGeographicDiagramLabelInterchangePlacementMixin import \
    ParallelGeographicDiagramLabelInterchangePlacementMixin
from .ParallelGeographicDiagramLabelOptionMixin import \
    ParallelGeographicDiagramLabelOptionMixin
from .ParallelGeographicDiagramLabelPayloadMixin import \
    ParallelGeographicDiagramLabelPayloadMixin
from .ParallelGeographicDiagramLabelRefineFlowMixin import \
    ParallelGeographicDiagramLabelRefineFlowMixin
from .ParallelGeographicDiagramLabelStationCandidatesMixin import \
    ParallelGeographicDiagramLabelStationCandidatesMixin
from .ParallelGeographicDiagramLabelStationPlacementMixin import \
    ParallelGeographicDiagramLabelStationPlacementMixin
from .ParallelGeographicDiagramLabelTextMixin import \
    ParallelGeographicDiagramLabelTextMixin
from .ParallelGeographicDiagramPathMixin import \
    ParallelGeographicDiagramPathMixin
from .ParallelGeographicDiagramRouteBuildMixin import \
    ParallelGeographicDiagramRouteBuildMixin
from .ParallelGeographicDiagramRouteGeometryMixin import \
    ParallelGeographicDiagramRouteGeometryMixin
from .ParallelGeographicDiagramStationSvgMixin import \
    ParallelGeographicDiagramStationSvgMixin
from .ParallelGeographicDiagramStyleMixin import \
    ParallelGeographicDiagramStyleMixin
from .ParallelGeographicDiagramSvgMarkupMixin import \
    ParallelGeographicDiagramSvgMarkupMixin
from .ParallelGeographicDiagramTickGeometryMixin import \
    ParallelGeographicDiagramTickGeometryMixin
from .ParallelGeographicDiagramTickPlacementMixin import \
    ParallelGeographicDiagramTickPlacementMixin


class ParallelGeographicDiagram(
    ParallelGeographicDiagramStyleMixin,
    ParallelGeographicDiagramCoreMixin,
    ParallelGeographicDiagramSvgMarkupMixin,
    ParallelGeographicDiagramStationSvgMixin,
    ParallelGeographicDiagramLabelTextMixin,
    ParallelGeographicDiagramPathMixin,
    ParallelGeographicDiagramRouteBuildMixin,
    ParallelGeographicDiagramRouteGeometryMixin,
    ParallelGeographicDiagramTickPlacementMixin,
    ParallelGeographicDiagramTickGeometryMixin,
    ParallelGeographicDiagramLabelInterchangePlacementMixin,
    ParallelGeographicDiagramLabelInterchangeCandidatesMixin,
    ParallelGeographicDiagramLabelStationPlacementMixin,
    ParallelGeographicDiagramLabelStationCandidatesMixin,
    ParallelGeographicDiagramLabelPayloadMixin,
    ParallelGeographicDiagramLabelOptionMixin,
    ParallelGeographicDiagramLabelRefineFlowMixin,
    ParallelGeographicDiagramLabelBoundsMixin,
    GeographicDiagram,
):
    pass
