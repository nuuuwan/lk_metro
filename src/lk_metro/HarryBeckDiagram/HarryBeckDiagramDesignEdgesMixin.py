class HarryBeckDiagramDesignEdgesMixin:
    def _build_design_edge_routes(self) -> dict[tuple[str, str], list[str]]:
        edge_routes = {}
        for route in self.routes:
            for segment in self._segments_by_route[route.id]:
                for first, second in zip(
                    segment["stops"], segment["stops"][1:]
                ):
                    edge = self._edge_key(first, second)
                    self._add_design_edge(
                        edge_routes, edge, first, second, route.id
                    )
        return edge_routes

    def _add_design_edge(
        self,
        edge_routes: dict[tuple[str, str], list[str]],
        edge: tuple[str, str],
        first: str,
        second: str,
        route_id: str,
    ) -> None:
        if edge not in edge_routes:
            edge_routes[edge] = []
            self._edge_directions[edge] = (first, second)
        if route_id not in edge_routes[edge]:
            edge_routes[edge].append(route_id)
