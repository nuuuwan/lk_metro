from lk_metro.PGD.PGDLabelInterchangeCandidatesMixin import \
    PGDLabelInterchangeCandidatesMixin
from lk_metro.PGD.PGDLabelInterchangePlacementMixin import \
    PGDLabelInterchangePlacementMixin


class PGDLabelInterchangeMixin(
    PGDLabelInterchangePlacementMixin,
    PGDLabelInterchangeCandidatesMixin,
):
    pass
