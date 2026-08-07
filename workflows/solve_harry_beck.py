import heapq
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

import networkx as nx

ROOT_DIR = Path(__file__).resolve().parents[1]
DIRECTIONS = {
    (1, 0): "E",
    (1, 1): "SE",
    (0, 1): "S",
    (-1, 1): "SW",
    (-1, 0): "W",
    (-1, -1): "NW",
    (0, -1): "N",
    (1, -1): "NE",
}
PORT_LENGTH = 256


def edge_key(first: str, second: str) -> tuple[str, str]:
    return tuple(sorted((first, second)))


def digital_line(
    start: tuple[int, int],
    end: tuple[int, int],
) -> list[tuple[int, int]]:
    x_coordinate, y_coordinate = start
    x_delta = abs(end[0] - x_coordinate)
    y_delta = abs(end[1] - y_coordinate)
    x_step = 1 if x_coordinate < end[0] else -1
    y_step = 1 if y_coordinate < end[1] else -1
    error = x_delta - y_delta
    path = [start]
    while (x_coordinate, y_coordinate) != end:
        doubled_error = error * 2
        if doubled_error > -y_delta:
            error -= y_delta
            x_coordinate += x_step
        if doubled_error < x_delta:
            error += x_delta
            y_coordinate += y_step
        path.append((x_coordinate, y_coordinate))
    return path


def route_corridor(
    start: tuple[int, int],
    end: tuple[int, int],
    blocked: set[tuple[int, int]],
    segments: dict[tuple[tuple[int, int], tuple[int, int]], tuple[str, str]],
) -> list[tuple[int, int]]:
    padding = 32
    min_x, max_x = sorted((start[0], end[0]))
    min_y, max_y = sorted((start[1], end[1]))
    queue = [(0, 0, 0, start)]
    previous = {start: None}
    distances = {start: 0}
    while queue:
        _, _, distance, current = heapq.heappop(queue)
        if current == end:
            path = []
            while current is not None:
                path.append(current)
                current = previous[current]
            return list(reversed(path))
        if distance != distances[current]:
            continue
        for delta in DIRECTIONS:
            candidate = (current[0] + delta[0], current[1] + delta[1])
            if not (
                min_x - padding <= candidate[0] <= max_x + padding
                and min_y - padding <= candidate[1] <= max_y + padding
            ):
                continue
            if candidate != end and candidate in blocked:
                continue
            if delta[0] and delta[1]:
                opposite = tuple(
                    sorted(
                        (
                            (current[0], candidate[1]),
                            (candidate[0], current[1]),
                        )
                    )
                )
                if opposite in segments:
                    continue
            candidate_distance = distance + 1
            if candidate_distance >= distances.get(candidate, math.inf):
                continue
            distances[candidate] = candidate_distance
            previous[candidate] = current
            heuristic = max(
                abs(candidate[0] - end[0]), abs(candidate[1] - end[1])
            )
            deviation = abs(
                (candidate[0] - start[0]) * (end[1] - start[1])
                - (candidate[1] - start[1]) * (end[0] - start[0])
            )
            heapq.heappush(
                queue,
                (
                    candidate_distance + heuristic,
                    deviation,
                    candidate_distance,
                    candidate,
                ),
            )
    raise RuntimeError(f"Could not route corridor from {start} to {end}")


def compress_tokens(tokens: list[str]) -> str:
    compressed = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        next_index = index + 1
        while next_index < len(tokens) and tokens[next_index] == token:
            next_index += 1
        count = next_index - index
        compressed.append(f"{count if count > 1 else ''}{token}")
        index = next_index
    return "-".join(compressed)


def assign_ports(
    graph: nx.Graph,
    positions: dict[str, tuple[int, int]],
) -> dict[tuple[str, str], tuple[int, int]]:
    ports = {}
    for name in graph:
        origin = positions[name]
        neighbors = sorted(
            graph[name],
            key=lambda neighbor: math.atan2(
                positions[neighbor][1] - origin[1],
                positions[neighbor][0] - origin[0],
            ),
        )
        target_angles = [
            math.atan2(
                positions[neighbor][1] - origin[1],
                positions[neighbor][0] - origin[0],
            )
            for neighbor in neighbors
        ]
        directions = min(
            itertools.permutations(DIRECTIONS, len(neighbors)),
            key=lambda candidates: sum(
                abs(
                    math.atan2(
                        math.sin(
                            math.atan2(candidate[1], candidate[0])
                            - target_angle
                        ),
                        math.cos(
                            math.atan2(candidate[1], candidate[0])
                            - target_angle
                        ),
                    )
                )
                for candidate, target_angle in zip(candidates, target_angles)
            ),
        )
        for neighbor, direction in zip(neighbors, directions):
            ports[(name, neighbor)] = direction
    return ports


def main() -> None:
    routes = json.loads((ROOT_DIR / "data" / "routes.json").read_text())
    edge_routes = defaultdict(list)
    graph = nx.Graph()
    for route in routes:
        for first, second in zip(route["stops"], route["stops"][1:]):
            graph.add_edge(first, second)
            edge_routes[edge_key(first, second)].append(route["id"])

    is_planar, embedding = nx.check_planarity(graph)
    if not is_planar:
        raise RuntimeError("Route graph is not planar")
    planar_positions = nx.combinatorial_embedding_to_pos(
        embedding,
        fully_triangulate=True,
    )
    positions = {
        name: tuple(value * 20 for value in point)
        for name, point in planar_positions.items()
    }
    if len(set(positions.values())) != len(positions):
        raise RuntimeError("Station positions overlap")

    ports = assign_ports(graph, positions)
    port_lengths = {
        (name, neighbor): min(
            PORT_LENGTH,
            max(
                1,
                max(
                    abs(positions[name][index] - positions[neighbor][index])
                    for index in range(2)
                )
                // 3,
            ),
        )
        for name, neighbor in ports
    }
    station_by_position = {point: name for name, point in positions.items()}
    for (name, neighbor), direction in ports.items():
        for distance in range(1, port_lengths[(name, neighbor)] + 1):
            point = tuple(
                positions[name][index] + direction[index] * distance
                for index in range(2)
            )
            if (
                point in station_by_position
                and station_by_position[point] != name
            ):
                port_lengths[(name, neighbor)] = max(1, distance - 1)
                break
    reserved_ports = {
        tuple(
            positions[name][index] + direction[index] * distance
            for index in range(2)
        )
        for (name, _), direction in ports.items()
        for distance in range(1, port_lengths[(name, _)] + 1)
    }
    paths = {}
    occupied = {point: name for name, point in positions.items()}
    drawn_segments = {}
    for edge, route_ids in sorted(
        edge_routes.items(),
        key=lambda item: -len(item[1]),
    ):
        first, second = edge
        first_ray = [
            tuple(
                positions[first][index]
                + ports[(first, second)][index] * distance
                for index in range(2)
            )
            for distance in range(1, port_lengths[(first, second)] + 1)
        ]
        second_ray = [
            tuple(
                positions[second][index]
                + ports[(second, first)][index] * distance
                for index in range(2)
            )
            for distance in range(1, port_lengths[(second, first)] + 1)
        ]
        first_port = first_ray[-1]
        second_port = second_ray[-1]
        middle = digital_line(first_port, second_port)
        path = [
            positions[first],
            *first_ray,
            *middle[1:-1],
            *reversed(second_ray),
            positions[second],
        ]
        for point in path[1:-1]:
            if point in occupied:
                raise RuntimeError(
                    f"Edge {edge} overlaps {occupied[point]!r} at {point}"
                )
            occupied[point] = edge
        for start, end in zip(path, path[1:]):
            segment = tuple(sorted((start, end)))
            if segment in drawn_segments:
                raise RuntimeError(
                    f"Edges {edge} and {drawn_segments[segment]} overlap"
                )
            drawn_segments[segment] = edge
        paths[edge] = path

    design_routes = {}
    for route in routes:
        tokens = []
        for first, second in zip(route["stops"], route["stops"][1:]):
            path = paths[edge_key(first, second)]
            if path[0] != positions[first]:
                path = list(reversed(path))
            for index, (start, end) in enumerate(zip(path, path[1:])):
                delta = (end[0] - start[0], end[1] - start[1])
                tokens.append(
                    ("b" if index < len(path) - 2 else "") + DIRECTIONS[delta]
                )
        design_routes[route["id"]] = compress_tokens(tokens)

    design = {
        "origin_stops": {
            name: list(point) for name, point in positions.items()
        },
        "routes": design_routes,
        "routes_backup_ignore": {},
    }
    print(json.dumps(design, indent=2))


if __name__ == "__main__":
    main()
