from lk_metro.PGD.PGDLabelBoundsGeometryMixin import \
    PGDLabelBoundsGeometryMixin
from lk_metro.PGD.PGDLabelBoundsIOMixin import PGDLabelBoundsIOMixin


class PGDLabelBoundsMixin(
    PGDLabelBoundsGeometryMixin,
    PGDLabelBoundsIOMixin,
):
    pass
