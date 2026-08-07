from lk_metro.PGD.PGDLabelStationCandidatesMixin import \
    PGDLabelStationCandidatesMixin
from lk_metro.PGD.PGDLabelStationPlacementMixin import \
    PGDLabelStationPlacementMixin


class PGDLabelStationMixin(
    PGDLabelStationPlacementMixin,
    PGDLabelStationCandidatesMixin,
):
    pass
