from .HarryBeckDiagramDesignEdgesMixin import HarryBeckDiagramDesignEdgesMixin
from .HarryBeckDiagramDesignReadMixin import HarryBeckDiagramDesignReadMixin
from .HarryBeckDiagramDesignSegmentsMixin import \
    HarryBeckDiagramDesignSegmentsMixin


class HarryBeckDiagramDesignProjectionMixin(
    HarryBeckDiagramDesignReadMixin,
    HarryBeckDiagramDesignSegmentsMixin,
    HarryBeckDiagramDesignEdgesMixin,
):
    pass
