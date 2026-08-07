from lk_metro.GeographicDiagram.Point import Point

Edge = tuple[str, str]
Bounds = tuple[float, float, float, float]
Tick = tuple[Point, Point]
CandidatePayload = tuple[Tick, Point, Point, float]
LabelOption = tuple[Bounds, CandidatePayload]
