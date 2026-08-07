from lk_metro.HBD.HBDDesignProjectionMixin import HBDDesignProjectionMixin
from lk_metro.HBD.HBDGeometryRoutesMixin import HBDGeometryRoutesMixin
from lk_metro.HBD.HBDI18nMixin import HBDI18nMixin
from lk_metro.HBD.HBDInitMixin import HBDInitMixin
from lk_metro.HBD.HBDLabelCacheMixin import HBDLabelCacheMixin
from lk_metro.HBD.HBDLabelPlacementMixin import HBDLabelPlacementMixin
from lk_metro.HBD.HBDLegendLayoutMixin import HBDLegendLayoutMixin
from lk_metro.HBD.HBDProjectionOpsMixin import HBDProjectionOpsMixin
from lk_metro.HBD.HBDRouteLabelPlacementMixin import \
    HBDRouteLabelPlacementMixin
from lk_metro.HBD.HBDSegmentIntersectionMixin import \
    HBDSegmentIntersectionMixin
from lk_metro.HBD.HBDStyleMixin import HBDStyleMixin
from lk_metro.HBD.HBDSvgMixin import HBDSvgMixin
from lk_metro.HBD.HBDTickOrientationMixin import HBDTickOrientationMixin
from lk_metro.Render.Render import Render


class HBD(
    HBDStyleMixin,
    HBDI18nMixin,
    HBDLabelCacheMixin,
    HBDLabelPlacementMixin,
    HBDTickOrientationMixin,
    HBDRouteLabelPlacementMixin,
    HBDInitMixin,
    HBDSvgMixin,
    HBDLegendLayoutMixin,
    HBDGeometryRoutesMixin,
    HBDSegmentIntersectionMixin,
    HBDDesignProjectionMixin,
    HBDProjectionOpsMixin,
    Render,
):
    pass
