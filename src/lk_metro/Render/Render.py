from lk_metro.GD.GD import GD
from lk_metro.Render.CoreMixin import CoreMixin
from lk_metro.Render.LabelBoundsMixin import LabelBoundsMixin
from lk_metro.Render.LabelInterchangeCandidatesMixin import \
    LabelInterchangeCandidatesMixin
from lk_metro.Render.LabelInterchangePlacementMixin import \
    LabelInterchangePlacementMixin
from lk_metro.Render.LabelOptionMixin import LabelOptionMixin
from lk_metro.Render.LabelPayloadMixin import LabelPayloadMixin
from lk_metro.Render.LabelRefineFlowMixin import LabelRefineFlowMixin
from lk_metro.Render.LabelStationCandidatesMixin import \
    LabelStationCandidatesMixin
from lk_metro.Render.LabelStationPlacementMixin import \
    LabelStationPlacementMixin
from lk_metro.Render.LabelTextMixin import LabelTextMixin
from lk_metro.Render.PathMixin import PathMixin
from lk_metro.Render.StationSvgMixin import StationSvgMixin
from lk_metro.Render.StyleMixin import StyleMixin
from lk_metro.Render.SvgMarkupMixin import SvgMarkupMixin
from lk_metro.Render.TickGeometryMixin import TickGeometryMixin
from lk_metro.Render.TickPlacementMixin import TickPlacementMixin


class Render(
    StyleMixin,
    CoreMixin,
    SvgMarkupMixin,
    StationSvgMixin,
    LabelTextMixin,
    PathMixin,
    TickPlacementMixin,
    TickGeometryMixin,
    LabelInterchangePlacementMixin,
    LabelInterchangeCandidatesMixin,
    LabelStationPlacementMixin,
    LabelStationCandidatesMixin,
    LabelPayloadMixin,
    LabelOptionMixin,
    LabelRefineFlowMixin,
    LabelBoundsMixin,
    GD,
):
    pass
