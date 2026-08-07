from lk_metro.GD.GD import GD
from lk_metro.PGD.PGDCoreMixin import PGDCoreMixin
from lk_metro.PGD.PGDLabelBoundsMixin import PGDLabelBoundsMixin
from lk_metro.PGD.PGDLabelInterchangeCandidatesMixin import \
    PGDLabelInterchangeCandidatesMixin
from lk_metro.PGD.PGDLabelInterchangePlacementMixin import \
    PGDLabelInterchangePlacementMixin
from lk_metro.PGD.PGDLabelOptionMixin import PGDLabelOptionMixin
from lk_metro.PGD.PGDLabelPayloadMixin import PGDLabelPayloadMixin
from lk_metro.PGD.PGDLabelRefineFlowMixin import PGDLabelRefineFlowMixin
from lk_metro.PGD.PGDLabelStationCandidatesMixin import \
    PGDLabelStationCandidatesMixin
from lk_metro.PGD.PGDLabelStationPlacementMixin import \
    PGDLabelStationPlacementMixin
from lk_metro.PGD.PGDLabelTextMixin import PGDLabelTextMixin
from lk_metro.PGD.PGDPathMixin import PGDPathMixin
from lk_metro.PGD.PGDRouteBuildMixin import PGDRouteBuildMixin
from lk_metro.PGD.PGDRouteGeometryMixin import PGDRouteGeometryMixin
from lk_metro.PGD.PGDStationSvgMixin import PGDStationSvgMixin
from lk_metro.PGD.PGDStyleMixin import PGDStyleMixin
from lk_metro.PGD.PGDSvgMarkupMixin import PGDSvgMarkupMixin
from lk_metro.PGD.PGDTickGeometryMixin import PGDTickGeometryMixin
from lk_metro.PGD.PGDTickPlacementMixin import PGDTickPlacementMixin


class PGD(
    PGDStyleMixin,
    PGDCoreMixin,
    PGDSvgMarkupMixin,
    PGDStationSvgMixin,
    PGDLabelTextMixin,
    PGDPathMixin,
    PGDRouteBuildMixin,
    PGDRouteGeometryMixin,
    PGDTickPlacementMixin,
    PGDTickGeometryMixin,
    PGDLabelInterchangePlacementMixin,
    PGDLabelInterchangeCandidatesMixin,
    PGDLabelStationPlacementMixin,
    PGDLabelStationCandidatesMixin,
    PGDLabelPayloadMixin,
    PGDLabelOptionMixin,
    PGDLabelRefineFlowMixin,
    PGDLabelBoundsMixin,
    GD,
):
    pass
