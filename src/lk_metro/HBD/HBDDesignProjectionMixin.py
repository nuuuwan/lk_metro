from lk_metro.HBD.HBDDesignEdgesMixin import HBDDesignEdgesMixin
from lk_metro.HBD.HBDDesignReadMixin import HBDDesignReadMixin
from lk_metro.HBD.HBDDesignSegmentsMixin import HBDDesignSegmentsMixin


class HBDDesignProjectionMixin(
    HBDDesignReadMixin,
    HBDDesignSegmentsMixin,
    HBDDesignEdgesMixin,
):
    pass
