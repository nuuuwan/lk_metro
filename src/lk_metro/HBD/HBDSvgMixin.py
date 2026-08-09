import html
import math

import qrcode

from lk_metro.GD.Point import Point


class HBDSvgMixin:
    SEA_COAST_STOPS = (
        "Williams Junc.",
        "Dehiwala",
        "Mount Lavinia",
        "Ratmalana",
        "Maliban Junc.",
        "Rathmalana Tech",
    )

    def _route_path_data(self, segments: list[list[Point]]) -> str:
        points = []
        for segment in segments:
            if points and points[-1] == segment[0]:
                points.extend(segment[1:])
            else:
                points.extend(segment)
        points = [
            point
            for index, point in enumerate(points)
            if index == 0 or point != points[index - 1]
        ]
        first = points[0]
        commands = [f"M {first[0]:g},{first[1]:g}"]
        for index, point in enumerate(points[1:-1], start=1):
            commands.extend(
                self._rounded_route_corner_commands(
                    points[index - 1], point, points[index + 1]
                )
            )
        end = points[-1]
        commands.append(f"L {end[0]:g},{end[1]:g}")
        return " ".join(commands)

    def _rounded_route_corner_commands(
        self,
        before: Point,
        point: Point,
        after: Point,
    ) -> list[str]:
        before_length = math.dist(before, point)
        after_length = math.dist(point, after)
        if math.isclose(before_length, 0) or math.isclose(after_length, 0):
            return []
        incoming_vector = self._unit_vector(point, before, before_length)
        outgoing_vector = self._unit_vector(point, after, after_length)
        cross_product = (
            incoming_vector[0] * outgoing_vector[1]
            - incoming_vector[1] * outgoing_vector[0]
        )
        if math.isclose(cross_product, 0, abs_tol=1e-9):
            return [f"L {point[0]:g},{point[1]:g}"]
        offset = min(
            self.ROUTE_CORNER_RADIUS, before_length / 2, after_length / 2
        )
        incoming = (
            point[0] + incoming_vector[0] * offset,
            point[1] + incoming_vector[1] * offset,
        )
        outgoing = (
            point[0] + outgoing_vector[0] * offset,
            point[1] + outgoing_vector[1] * offset,
        )
        control_distance = offset * 0.55
        first_control = (
            incoming[0] - incoming_vector[0] * control_distance,
            incoming[1] - incoming_vector[1] * control_distance,
        )
        second_control = (
            outgoing[0] - outgoing_vector[0] * control_distance,
            outgoing[1] - outgoing_vector[1] * control_distance,
        )
        return [
            f"L {incoming[0]:g},{incoming[1]:g}",
            f"C {first_control[0]:g},{first_control[1]:g} "
            f"{second_control[0]:g},{second_control[1]:g} "
            f"{outgoing[0]:g},{outgoing[1]:g}",
        ]

    @staticmethod
    def _unit_vector(start: Point, end: Point, length: float) -> Point:
        return ((end[0] - start[0]) / length, (end[1] - start[1]) / length)

    def _station_marker_svg_line(
        self,
        stop_name: str,
        position: Point,
        memberships: dict[str, set[str]],
        route_colors: dict[str, str],
    ) -> str:
        tick = getattr(self, "_station_ticks", {}).get(stop_name)
        if tick is None:
            if len(memberships[stop_name]) > 1:
                return self._interchange_capsule_svg(stop_name)
            return super()._station_marker_svg_line(
                stop_name, position, memberships, route_colors
            )
        route_id = next(iter(memberships[stop_name]))
        return (
            f'<line class="station" x1="{tick[0][0]}" y1="{tick[0][1]}" '
            f'x2="{tick[1][0]}" y2="{tick[1][1]}" '
            f'stroke="{route_colors[route_id]}" stroke-linecap="square"/>'
        )

    def _interchange_capsule_svg(self, stop_name: str) -> str:
        points = self._interchange_route_points(stop_name)
        first, second, inner_width = self._interchange_capsule_geometry(
            points
        )
        outer_width = inner_width + 2 * self.INTERCHANGE_STROKE_WIDTH
        coordinates = (
            f'x1="{first[0]:g}" y1="{first[1]:g}" '
            f'x2="{second[0]:g}" y2="{second[1]:g}"'
        )
        return (
            f'<g class="interchange-capsule">'
            f'<line {coordinates} stroke="#000000" '
            f'stroke-width="{outer_width:g}" stroke-linecap="round"/>'
            f'<line {coordinates} stroke="#ffffff" '
            f'stroke-width="{inner_width:g}" stroke-linecap="round"/>'
            "</g>"
        )

    def _interchange_capsule_geometry(
        self,
        points: list[Point],
    ) -> tuple[Point, Point, float]:
        center = (
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
        )
        axis = self._interchange_capsule_axis(points, center)
        normal = (-axis[1], axis[0])
        projections = [
            (point[0] - center[0]) * axis[0]
            + (point[1] - center[1]) * axis[1]
            for point in points
        ]
        half_length = (max(projections) - min(projections)) / 2
        half_length = max(half_length, self.STATION_RADIUS)
        axis_center = (
            center[0] + (max(projections) + min(projections)) * axis[0] / 2,
            center[1] + (max(projections) + min(projections)) * axis[1] / 2,
        )
        half_width = (
            self.STATION_RADIUS
            + self.ROUTE_STROKE_WIDTH / 2
            + max(
                abs(
                    (point[0] - axis_center[0]) * normal[0]
                    + (point[1] - axis_center[1]) * normal[1]
                )
                for point in points
            )
        )
        first = (
            axis_center[0] - axis[0] * half_length,
            axis_center[1] - axis[1] * half_length,
        )
        second = (
            axis_center[0] + axis[0] * half_length,
            axis_center[1] + axis[1] * half_length,
        )
        return first, second, 2 * half_width

    def _interchange_route_points(self, stop_name: str) -> list[Point]:
        position = self._label_positions[stop_name]
        return [
            self._nearest_route_point(
                self._label_segments[route_id], position
            )
            for route_id in self._label_memberships[stop_name]
        ]

    @staticmethod
    def _nearest_route_point(
        route_segments: list[list[Point]],
        position: Point,
    ) -> Point:
        path_segments = [
            (first, second)
            for path in route_segments
            for first, second in zip(path, path[1:])
        ]
        return min(
            (
                HBDSvgMixin._closest_point_on_segment(position, first, second)
                for first, second in path_segments
            ),
            key=lambda point: math.dist(point, position),
        )

    @staticmethod
    def _closest_point_on_segment(
        point: Point,
        first: Point,
        second: Point,
    ) -> Point:
        delta = second[0] - first[0], second[1] - first[1]
        length_squared = delta[0] ** 2 + delta[1] ** 2
        if math.isclose(length_squared, 0.0, abs_tol=1e-9):
            return first
        projection = (
            (point[0] - first[0]) * delta[0]
            + (point[1] - first[1]) * delta[1]
        ) / length_squared
        fraction = min(1.0, max(0.0, projection))
        return (
            first[0] + fraction * delta[0],
            first[1] + fraction * delta[1],
        )

    @staticmethod
    def _interchange_capsule_axis(
        points: list[Point],
        center: Point,
    ) -> Point:
        x_variance = sum((point[0] - center[0]) ** 2 for point in points)
        y_variance = sum((point[1] - center[1]) ** 2 for point in points)
        covariance = sum(
            (point[0] - center[0]) * (point[1] - center[1])
            for point in points
        )
        if math.isclose(x_variance + y_variance, 0.0, abs_tol=1e-9):
            return (0.0, 1.0)
        angle = math.atan2(2 * covariance, x_variance - y_variance) / 2
        return math.cos(angle), math.sin(angle)

    def _route_svg_line(self, route, segments: list[list[Point]]) -> str:
        if route.id not in self._circle_routes:
            path_data = self._route_path_data(segments)
            return (
                f'<path class="route" d="{path_data}" '
                f'stroke="{route.color}" fill="none" '
                f'stroke-width="{self.ROUTE_STROKE_WIDTH:g}" '
                f'stroke-linecap="round" stroke-linejoin="round"/>'
            )
        center = self._circle_centers[route.id]
        center_x = (
            center[0] - self._grid_min_x
        ) * self.UNIT_SCALE + self.padding
        center_y = (
            center[1] - self._grid_min_y
        ) * self.UNIT_SCALE + self.padding
        x_radius = self._circle_routes[route.id][1] * self.UNIT_SCALE
        y_radius = self._circle_routes[route.id][2] * self.UNIT_SCALE
        return (
            f'<ellipse class="route" cx="{center_x:g}" cy="{center_y:g}" '
            f'rx="{x_radius:g}" ry="{y_radius:g}" '
            f'stroke="{route.color}" fill="none" '
            f'stroke-width="{self.ROUTE_STROKE_WIDTH:g}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )

    def _route_svg_lines(
        self,
        segments: dict[str, list[list[Point]]],
    ) -> list[str]:
        routes = sorted(self.routes, key=lambda route: route.id == "CM02")
        return [
            self._route_svg_line(route, segments[route.id])
            for route in routes
        ]

    def _route_name_svg_lines(self) -> list[str]:
        routes_by_id = {route.id: route for route in self.routes}
        lines = []
        for route_id, (
            x_coordinate,
            y_coordinate,
            angle,
        ) in self._route_name_positions.items():
            route = routes_by_id[route_id]
            transform = f' transform="rotate({angle} {x_coordinate} '
            transform += f'{y_coordinate})"'
            transform = transform if angle else ""
            lines.append(
                f'<text class="route-name" x="{x_coordinate}" '
                f'y="{y_coordinate}" '
                f'text-anchor="middle" fill="{route.color}"{transform}>'
                f"{html.escape(route.id)}</text>"
            )
        return lines

    def _route_name_bounds(
        self,
    ) -> list[tuple[str, tuple[float, float, float, float]]]:
        return [
            (f"route ID {route_id}", bounds)
            for route_id, bounds in self._route_name_bounds_by_id.items()
        ]

    def _background_svg_lines(self) -> list[str]:
        return [
            *self._sea_svg_lines(),
            *self._beira_lake_svg_lines(),
            *self._diyawanna_lake_svg_lines(),
            *self._bolgoda_lake_svg_lines(),
            *self._kelani_river_svg_lines(),
            *self._viharamahadevi_park_svg_lines(),
            *self._borella_cemetery_svg_lines(),
            *self._royal_colombo_golf_course_svg_lines(),
            *self._github_qr_svg_lines(),
        ]

    def _github_qr_svg_lines(self) -> list[str]:
        qr_code = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            border=4,
        )
        qr_code.add_data(self.GITHUB_REPO_URL)
        qr_code.make(fit=True)
        matrix = qr_code.get_matrix()
        module_size = self.GITHUB_QR_SIZE / len(matrix)
        x_coordinate = -self._content_offset()[0] + self.GITHUB_QR_MARGIN
        canvas_bottom = (
            self._svg_dimensions()[1]
            - self._content_offset()[1]
            - self.TITLE_HEIGHT
        )
        y_coordinate = (
            canvas_bottom - self.GITHUB_QR_MARGIN - self.GITHUB_QR_SIZE
        )
        modules = " ".join(
            f"M {x_coordinate + column * module_size:g},"
            f"{y_coordinate + row * module_size:g} "
            f"h {module_size:g} v {module_size:g} "
            f"h {-module_size:g} Z"
            for row, values in enumerate(matrix)
            for column, is_dark in enumerate(values)
            if is_dark
        )
        return [
            f'<a class="github-qr" href="{html.escape(self.GITHUB_REPO_URL)}" '
            'aria-label="Lanka Metro GitHub repository">',
            f'<rect x="{x_coordinate:g}" y="{y_coordinate:g}" '
            f'width="{self.GITHUB_QR_SIZE:g}" '
            f'height="{self.GITHUB_QR_SIZE:g}" rx="0.5" fill="#ffffff"/>',
            f'<path d="{modules}" fill="{self.TEXT_COLOR}"/>',
            "</a>",
        ]

    def _viharamahadevi_park_svg_lines(self) -> list[str]:
        required = ("Town Hall", "Nelum Pokuna", "Public Library")
        if not all(name in self._logical_positions for name in required):
            return []
        town_hall = self._background_stop_position("Town Hall")
        nelum_pokuna = self._background_stop_position("Nelum Pokuna")
        public_library = self._background_stop_position("Public Library")
        points = (
            (town_hall[0] + 1, town_hall[1] - 2),
            (nelum_pokuna[0] - 1, nelum_pokuna[1] + 1),
            (nelum_pokuna[0] - 1, nelum_pokuna[1] + 5),
            (public_library[0] + 2, public_library[1] - 1),
        )
        return self._green_space_svg_lines(
            "viharamahadevi-park", points, None
        )

    def _borella_cemetery_svg_lines(self) -> list[str]:
        borella = self._background_stop_position("Borella")
        castle_hospital = self._background_stop_position("Castle Hosp.")
        points = (
            (borella[0] + 2, castle_hospital[1] + 2),
            (castle_hospital[0] + 5, castle_hospital[1] + 2),
            (castle_hospital[0] + 5, castle_hospital[1] + 8),
            (castle_hospital[0], castle_hospital[1] + 11),
            (borella[0] + 2, castle_hospital[1] + 9),
        )
        return self._green_space_svg_lines(
            "borella-cemetery", points, "Borella Cemetery"
        )

    def _royal_colombo_golf_course_svg_lines(self) -> list[str]:
        castle_hospital = self._background_stop_position("Castle Hosp.")
        army_hospital = self._background_stop_position("Army Hosp.")
        points = (
            (army_hospital[0] + 2, castle_hospital[1] + 13),
            (castle_hospital[0] + 7, castle_hospital[1] + 10),
            (castle_hospital[0] + 8, army_hospital[1] - 2),
            (army_hospital[0] + 3, army_hospital[1] - 1),
        )
        return self._green_space_svg_lines(
            "royal-colombo-golf-course",
            points,
            "Royal Colombo Golf Course",
        )

    def _sea_svg_lines(self) -> list[str]:
        required = (
            "New Kelani Br.",
            "Colombo Fort",
            "Kollupitiya",
            "Wellawatta",
        ) + self.SEA_COAST_STOPS
        if not all(name in self._logical_positions for name in required):
            return []
        self._background_stop_position("New Kelani Br.")
        fort = self._background_stop_position("Colombo Fort")
        kollupitiya = self._background_stop_position("Kollupitiya")
        wellawatta = self._background_stop_position("Wellawatta")
        coast = tuple(
            self._background_stop_position(name)
            for name in self.SEA_COAST_STOPS
        )
        north_y = -self.TITLE_HEIGHT - self._content_offset()[1]
        left_x = -self._content_offset()[0] - self.FEATURE_CORNER_RADIUS
        shore_gap = self.UNIT_SCALE
        north_coast_x = fort[0] - self.ROUTE_STROKE_WIDTH
        coast_inset = 2
        points = (
            (left_x, north_y),
            (north_coast_x, north_y),
            (north_coast_x - coast_inset, north_y + coast_inset),
            (north_coast_x - coast_inset, fort[1] - 2),
            (north_coast_x, fort[1] + 4),
            (kollupitiya[0] - shore_gap, kollupitiya[1]),
            (wellawatta[0] - shore_gap, wellawatta[1]),
            *((point[0] - shore_gap, point[1]) for point in coast),
            (coast[-1][0] - shore_gap, 153),
            (self.width, 153),
            (self.width, self.height),
            (left_x, self.height),
        )
        return self._water_area_svg_lines(
            "sea", points, "Indian Ocean", (9, wellawatta[1] + 8)
        )

    def _beira_lake_svg_lines(self) -> list[str]:
        required = (
            "Town Hall",
            "Gamini Hall",
            "Regal Cinema",
            "Nawaloka",
            "Union Pl.",
        )
        if not all(name in self._logical_positions for name in required):
            return []
        town_hall = self._background_stop_position("Town Hall")
        gamini_hall = self._background_stop_position("Gamini Hall")
        regal_cinema = self._background_stop_position("Regal Cinema")
        nawaloka = self._background_stop_position("Nawaloka")
        union_place = self._background_stop_position("Union Pl.")
        points = (
            (regal_cinema[0] + 6, regal_cinema[1] + 6),
            (gamini_hall[0] - 5, gamini_hall[1] + 6),
            (town_hall[0] - 7, town_hall[1] - 6),
            (union_place[0] + 5, union_place[1] - 6),
            (nawaloka[0] + 6, nawaloka[1] - 6),
        )
        return self._water_area_svg_lines("beira-lake", points, None, None)

    def _diyawanna_lake_svg_lines(self) -> list[str]:
        required = ("Palam Thuna Junc.", "Isurupaya", "Thalawathugoda")
        if not all(name in self._logical_positions for name in required):
            return []
        palam_thuna = self._background_stop_position("Palam Thuna Junc.")
        isurupaya = self._background_stop_position("Isurupaya")
        thalawathugoda = self._background_stop_position("Thalawathugoda")
        points = (
            (palam_thuna[0] - 5, palam_thuna[1] + 5),
            (palam_thuna[0], palam_thuna[1] + 5),
            (isurupaya[0], isurupaya[1] + 5),
            (thalawathugoda[0], thalawathugoda[1] + 5),
            (thalawathugoda[0], thalawathugoda[1] + 8),
            (palam_thuna[0] - 5, thalawathugoda[1] + 8),
        )
        label_position = (
            (palam_thuna[0] - 5 + thalawathugoda[0]) / 2,
            thalawathugoda[1] + 6.5,
        )
        return self._water_area_svg_lines(
            "diyawanna-lake", points, "Diyawanna Lake", label_position
        )

    def _bolgoda_lake_svg_lines(self) -> list[str]:
        required = (
            "Raththanapitiya",
            "Lanka Fiber",
            "Jayanthi Mw.",
            "Palam Junc.",
        )
        if not all(name in self._logical_positions for name in required):
            return []
        raththanapitiya = self._background_stop_position("Raththanapitiya")
        lanka_fiber = self._background_stop_position("Lanka Fiber")
        jayanthi = self._background_stop_position("Jayanthi Mw.")
        palam = self._background_stop_position("Palam Junc.")
        outlet_left = jayanthi[0] + 2
        outlet_right = palam[0] - 2
        points = (
            (raththanapitiya[0], raththanapitiya[1] + 2),
            (lanka_fiber[0], lanka_fiber[1] + 2),
            (outlet_right, palam[1] - 7),
            (outlet_right, 153),
            (outlet_left, 153),
            (outlet_left, jayanthi[1] - 2),
            (lanka_fiber[0] + 2, lanka_fiber[1] + 7),
            (raththanapitiya[0], raththanapitiya[1] + 7),
        )
        label_position = (
            (raththanapitiya[0] + lanka_fiber[0]) / 2,
            raththanapitiya[1] + 4.5,
        )
        return self._water_area_svg_lines(
            "bolgoda-lake", points, "Bolgoda Lake", label_position
        )

    def _kelani_river_svg_lines(self) -> list[str]:
        if "New Kelani Br." not in self._logical_positions:
            return []
        bridge_x, bridge_y = self._background_stop_position("New Kelani Br.")
        diagonal_half_span = 26
        upper_y = bridge_y - diagonal_half_span
        lower_y = bridge_y + diagonal_half_span
        river_path = (
            f"M -4,{upper_y:g} "
            f"L {bridge_x - diagonal_half_span:g},{upper_y:g} "
            f"L {bridge_x + diagonal_half_span:g},{lower_y:g} "
            f"L {self.width + 4:g},{lower_y:g}"
        )
        label_x = (bridge_x + diagonal_half_span + self.width + 4) / 2
        return [
            f'<path d="{river_path}" fill="none" '
            f'stroke="{self.WATER_FEATURE_COLOR}" '
            'stroke-width="3.5" stroke-linecap="round" '
            'stroke-linejoin="round"/>',
            f'<text x="{label_x:g}" y="{lower_y:g}" text-anchor="middle" '
            'dominant-baseline="middle" '
            'font-family="Gill Sans, sans-serif" font-size="1.6" '
            'font-style="italic" fill="#287f98">Kelani River</text>',
        ]

    def _background_stop_position(self, stop_name: str) -> Point:
        x_coordinate, y_coordinate = self._logical_positions[stop_name]
        return (
            (x_coordinate - self._grid_min_x) * self.UNIT_SCALE
            + self.padding,
            (y_coordinate - self._grid_min_y) * self.UNIT_SCALE
            + self.padding,
        )

    def _water_area_svg_lines(
        self,
        css_class: str,
        points: tuple[Point, ...],
        label: str | None,
        label_position: Point | None,
    ) -> list[str]:
        path = self._rounded_closed_path(points)
        lines = [
            f'<path class="water-feature {css_class}" d="{path}" '
            f'fill="{self.WATER_FEATURE_COLOR}"/>',
        ]
        if label is None or label_position is None:
            return lines
        lines.append(
            f'<text class="water-label" x="{label_position[0]:g}" '
            f'y="{label_position[1]:g}" text-anchor="middle" '
            'dominant-baseline="middle" '
            'font-family="Gill Sans, sans-serif" font-size="1.6" '
            f'font-style="italic" fill="#287f98">{label}</text>'
        )
        return lines

    def _green_space_svg_lines(
        self,
        css_class: str,
        points: tuple[Point, ...],
        label: str | None,
    ) -> list[str]:
        path = self._rounded_closed_path(points)
        lines = [
            f'<path class="green-space {css_class}" d="{path}" '
            f'fill="{self.GREEN_SPACE_COLOR}"/>',
        ]
        if label is None:
            return lines
        label_x = sum(point[0] for point in points) / len(points)
        label_y = sum(point[1] for point in points) / len(points)
        lines.append(
            f'<text class="green-space-label" x="{label_x:g}" '
            f'y="{label_y:g}" text-anchor="middle" '
            'dominant-baseline="middle" '
            f'font-family="Gill Sans, sans-serif" '
            f'font-size="{self.GREEN_SPACE_LABEL_FONT_SIZE:g}" '
            f'font-style="italic" fill="{self.GREEN_SPACE_LABEL_COLOR}">'
            f"{label}</text>"
        )
        return lines

    def _rounded_closed_path(self, points: tuple[Point, ...]) -> str:
        points = tuple(
            point
            for index, point in enumerate(points)
            if point != points[index - 1]
        )
        corners = []
        for index, current in enumerate(points):
            previous = points[index - 1]
            following = points[(index + 1) % len(points)]
            previous_length = math.dist(current, previous)
            following_length = math.dist(current, following)
            offset = min(
                self.FEATURE_CORNER_RADIUS,
                previous_length / 2,
                following_length / 2,
            )
            incoming = (
                current[0]
                + (previous[0] - current[0]) * offset / previous_length,
                current[1]
                + (previous[1] - current[1]) * offset / previous_length,
            )
            outgoing = (
                current[0]
                + (following[0] - current[0]) * offset / following_length,
                current[1]
                + (following[1] - current[1]) * offset / following_length,
            )
            corners.append((incoming, current, outgoing))
        commands = [f"M {corners[0][0][0]:g},{corners[0][0][1]:g}"]
        for incoming, corner, outgoing in corners:
            if incoming != corners[0][0]:
                commands.append(f"L {incoming[0]:g},{incoming[1]:g}")
            commands.append(
                f"Q {corner[0]:g},{corner[1]:g} "
                f"{outgoing[0]:g},{outgoing[1]:g}"
            )
        commands.append("Z")
        return " ".join(commands)

    @property
    def complexity_by_route(self) -> dict[str, int]:
        return {
            route.id: (
                1
                if route.id in self._circle_routes
                else sum(
                    index == 0
                    or segment["direction"]
                    != segments[index - 1]["direction"]
                    for index, segment in enumerate(segments)
                )
            )
            for route in self.routes
            for segments in [self._segments_by_route[route.id]]
        }

    @property
    def complexity(self) -> int:
        return sum(self.complexity_by_route.values())
