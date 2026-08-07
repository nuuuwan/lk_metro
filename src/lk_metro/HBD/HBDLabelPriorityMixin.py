class HBDLabelPriorityMixin:
    def _label_priority(
        self,
        stop_name: str,
        memberships: dict[str, set[str]],
        potential_count: int,
    ) -> tuple[int, int, str]:
        if self._is_terminus(stop_name):
            tier = 0
        elif len(memberships[stop_name]) > 1:
            tier = 1
        else:
            tier = 2
        return potential_count, tier, stop_name
