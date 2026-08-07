from lk_metro.HarryBeckDiagram.HarryBeckDiagramDesignEdgesMixin import \
    HarryBeckDiagramDesignEdgesMixin
from lk_metro.HarryBeckDiagram.HarryBeckDiagramDesignReadMixin import \
    HarryBeckDiagramDesignReadMixin
from lk_metro.HarryBeckDiagram.HarryBeckDiagramDesignSegmentsMixin import \
    HarryBeckDiagramDesignSegmentsMixin


class HarryBeckDiagramDesignProjectionMixin(
    HarryBeckDiagramDesignReadMixin,
    HarryBeckDiagramDesignSegmentsMixin,
    HarryBeckDiagramDesignEdgesMixin,
):
    pass
