from lk_metro.HBD.HBDGeometryEdgeValidationMixin import \
    HBDGeometryEdgeValidationMixin
from lk_metro.HBD.HBDGeometryOverlapCrossingMixin import \
    HBDGeometryOverlapCrossingMixin


class HBDGeometryErrorsMixin(
    HBDGeometryEdgeValidationMixin,
    HBDGeometryOverlapCrossingMixin,
):
    pass
