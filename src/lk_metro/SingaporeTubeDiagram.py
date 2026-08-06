import html

from .HarryBeckDiagram import HarryBeckDiagram
from .Route import Route
from .Stop import Stop


class SingaporeTubeDiagram(HarryBeckDiagram):
	MAP_TITLE = "SYSTEM MAP"
	TITLE_HEIGHT = 14
	FOOTER_HEIGHT = 22
	BACKGROUND_COLOR = "#dcecf2"
	FONT_FAMILY = "'Helvetica Neue', Helvetica, Arial, sans-serif"
	ROUTE_STROKE_WIDTH = 0.9
	PARALLEL_ROUTE_GAP = 1.25
	LABEL_FONT_SIZE = 1.35
	TERMINAL_LABEL_FONT_SIZE = 1.35
	LABEL_OFFSET = 0.8
	CODE_BADGE_HEIGHT = 1.8
	CODE_BADGE_GAP = 0.16
	INTERCHANGE_RADIUS = 1.15
	INTERCHANGE_STROKE_WIDTH = 0.32
	ROUTE_NAME_POSITIONS = {}
	RIVER_PATH = ""

	def __init__(self, routes: list[Route], stops: list[Stop]) -> None:
		super().__init__(routes, stops)
		self._routes_by_id = {route.id: route for route in self.routes}
		self._station_codes = {
			stop.name: [
				(
					route.id,
					f"{int(route.id.removeprefix('CM'))}/"
					f"{route.stops.index(stop.name) + 1}",
				)
				for route in self.routes
				if stop.name in route.stops
			]
			for stop in self.stops
		}

	def _content_dimensions(self) -> tuple[int, int]:
		return self.width, self.height + self.TITLE_HEIGHT + self.FOOTER_HEIGHT

	def _background_svg_lines(self) -> list[str]:
		return [
			f'<path class="land" d="M 8,1 H {self.width - 12} '
			f'Q {self.width - 2},1 {self.width - 2},11 '
			f'V {self.height - 12} Q {self.width - 2},{self.height - 2} '
			f'{self.width - 12},{self.height - 2} H 12 '
			f'Q 2,{self.height - 2} 2,{self.height - 12} V 11 Q 2,1 8,1 Z"/>',
		]

	def _stop_label(self, stop_name: str) -> str:
		codes = " / ".join(code for _, code in self._station_codes[stop_name])
		return f"{codes} {stop_name}"

	def _code_badge_svg_lines(
		self,
		stop_name: str,
		x_coordinate: float,
		y_coordinate: float,
	) -> tuple[list[str], float]:
		badges = [
			(
				code,
				self._routes_by_id[route_id].color,
				max(3.8, len(code) * 0.52 + 1.0),
			)
			for route_id, code in self._station_codes[stop_name]
		]
		total_width = sum(width for _, _, width in badges) + self.CODE_BADGE_GAP * (
			len(badges) - 1
		)
		start_x = x_coordinate - total_width / 2
		lines = []
		for code, color, width in badges:
			lines.extend(
				[
					f'<rect class="station-code" x="{start_x}" '
					f'y="{y_coordinate - self.CODE_BADGE_HEIGHT / 2}" '
					f'width="{width}" height="{self.CODE_BADGE_HEIGHT}" '
					f'rx="{self.CODE_BADGE_HEIGHT / 2}" fill="{color}"/>',
					f'<text class="station-code-text" x="{start_x + width / 2}" '
					f'y="{y_coordinate}" text-anchor="middle">'
					f'{html.escape(code)}</text>',
				]
			)
			start_x += width + self.CODE_BADGE_GAP
		return lines, total_width

	def _title_and_legend_svg_lines(self) -> list[str]:
		lines = [
			f'<rect class="header" x="0" y="0" width="{self.width}" '
			f'height="{self.TITLE_HEIGHT}"/>',
			'<circle cx="7" cy="7" r="3.6" fill="#008b95" '
			'stroke="#f2c84b" stroke-width="0.55"/>',
			'<path d="M 4.8,7 L 6.2,5.6 L 9.2,8.4" fill="none" '
			'stroke="white" stroke-width="0.7" stroke-linecap="round"/>',
			f'<text class="system-title" x="13" y="8.7">{self.MAP_TITLE}</text>',
			f'<rect class="footer" x="0" y="{self.TITLE_HEIGHT + self.height}" '
			f'width="{self.width}" height="{self.FOOTER_HEIGHT}"/>',
			f'<text class="legend-heading" x="4" '
			f'y="{self.TITLE_HEIGHT + self.height + 4}">LINES</text>',
		]
		legend_y = self.TITLE_HEIGHT + self.height + 8
		column_width = self.width / 4
		for index, route in enumerate(self.legend_routes):
			column = index % 4
			row = index // 4
			x_coordinate = 4 + column * column_width
			y_coordinate = legend_y + row * 4.5
			line_code = f"C{int(route.id.removeprefix('CM'))}"
			lines.extend(
				[
					f'<rect x="{x_coordinate}" y="{y_coordinate - 1.3}" '
					f'width="5" height="2" rx="0.5" fill="{route.color}"/>',
					f'<text class="legend-code" x="{x_coordinate + 2.5}" '
					f'y="{y_coordinate - 0.28}" text-anchor="middle">{line_code}</text>',
					f'<text class="legend-text" x="{x_coordinate + 6}" '
					f'y="{y_coordinate - 0.25}">{html.escape(route.name)}</text>',
				]
			)
		lines.append(
			f'<text class="source" x="{self.width - 4}" '
			f'y="{self.TITLE_HEIGHT + self.height + self.FOOTER_HEIGHT - 2}" '
			'text-anchor="end">Source data: lankametro.lk</text>'
		)
		return lines

	def to_svg(self) -> str:
		positions = self.layout()
		segments = self.route_segments(positions)
		memberships = self._route_memberships()
		station_ticks = self.station_ticks(positions, segments, memberships)
		svg_width, svg_height = self._svg_dimensions()
		content_x, content_y = self._content_offset()
		lines = [
			'<?xml version="1.0" encoding="UTF-8"?>',
			f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" '
			f'height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">',
			"<style>",
			f"text {{ font-family: {self.FONT_FAMILY}; }}",
			".header { fill: #292a26; }",
			".footer, .land { fill: #ffffff; }",
			".route { fill: none; stroke-linecap: round; stroke-linejoin: round; }",
			f".station-name {{ font-size: {self.LABEL_FONT_SIZE}px; fill: #111; "
			"dominant-baseline: middle; paint-order: stroke; stroke: white; "
			"stroke-width: 0.35; }",
			".terminal-name { font-weight: bold; }",
			".station-code-text, .legend-code { font-size: 0.72px; "
			"font-weight: bold; fill: white; dominant-baseline: middle; }",
			".system-title { font-size: 5.2px; font-weight: 500; fill: white; }",
			".legend-heading { font-size: 1.2px; font-weight: bold; fill: #222; }",
			".legend-text { font-size: 0.92px; fill: #222; }",
			".source { font-size: 0.85px; fill: #555; }",
			"</style>",
			f'<rect width="{svg_width}" height="{svg_height}" '
			f'fill="{self.BACKGROUND_COLOR}"/>',
			f'<g transform="translate({content_x} {content_y})">',
			f'<g transform="translate(0 {self.TITLE_HEIGHT})">',
			*self._background_svg_lines(),
		]
		for route in self.routes:
			lines.append(
				f'<path class="route" d="{self._route_path_data(segments[route.id])}" '
				f'stroke="{route.color}" stroke-width="{self.ROUTE_STROKE_WIDTH}"/>'
			)

		for stop in self.stops:
			x_coordinate, y_coordinate = positions[stop.name]
			route_ids = sorted(memberships[stop.name], key=self._route_order.__getitem__)
			if len(route_ids) > 1:
				label_x, label_y, text_anchor = self._interchange_label_positions[stop.name]
			else:
				label_x, label_y = self._station_label_positions[stop.name]
				text_anchor = self._station_label_text_anchors[stop.name]
			badge_lines, _ = self._code_badge_svg_lines(
				stop.name,
				x_coordinate,
				y_coordinate,
			)
			lines.extend(badge_lines)
			label_class = (
				"station-name terminal-name"
				if self._is_terminus(stop.name)
				else "station-name"
			)
			lines.append(
				f'<text class="{label_class}" x="{label_x}" y="{label_y}" '
				f'text-anchor="{text_anchor}">{html.escape(stop.name)}</text>'
			)

		lines.extend(
			["</g>", *self._title_and_legend_svg_lines(), "</g>", "</svg>"]
		)
		return "\n".join(lines) + "\n"