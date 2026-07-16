from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import asin, cos, radians, sin, sqrt
from time import monotonic
from typing import Literal

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..config import get_settings
from ..schemas import AStarRouteRequest
from .location_service import require_location

RouteMode = Literal["walk", "drive"]
Coordinate = tuple[float, float]  # latitude, longitude
Adjacency = dict[int, list[tuple[int, float]]]

settings = get_settings()

# 동일한 두 장소의 반복 조회가 공용 Overpass 서버에 부담을 주지 않도록 짧게 메모리 캐시한다.
_ROUTE_CACHE: dict[tuple[str, str, str], tuple[float, dict]] = {}
_CACHE_SECONDS = 20 * 60
_CACHE_MAX_ITEMS = 128

_WALK_EXCLUDED = {
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "raceway",
    "construction",
    "proposed",
}
_DRIVE_EXCLUDED = {
    "footway",
    "path",
    "pedestrian",
    "steps",
    "cycleway",
    "bridleway",
    "corridor",
    "platform",
    "elevator",
    "construction",
    "proposed",
}


@dataclass(slots=True)
class RoadGraph:
    coordinates: dict[int, Coordinate]
    adjacency: Adjacency


class RouteGraphError(RuntimeError):
    pass


class RouteNotFoundError(RuntimeError):
    pass


def haversine_m(a: Coordinate, b: Coordinate) -> float:
    """두 위경도 좌표 사이의 대권거리를 미터로 계산한다."""
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6_371_000 * 2 * asin(min(1.0, sqrt(h)))


def _sample_line(start: Coordinate, end: Coordinate, spacing_m: float) -> list[Coordinate]:
    distance = haversine_m(start, end)
    segments = max(1, int(distance / spacing_m) + 1)
    return [
        (
            start[0] + (end[0] - start[0]) * index / segments,
            start[1] + (end[1] - start[1]) * index / segments,
        )
        for index in range(segments + 1)
    ]


def _overpass_query(start: Coordinate, end: Coordinate, mode: RouteMode, radius_m: int) -> str:
    # 출발지와 도착지를 잇는 직선 주변을 여러 원으로 나눠 조회한다.
    # 전체 사각형을 조회하는 것보다 불필요한 도로 노드 수가 크게 줄어든다.
    points = _sample_line(start, end, max(1200.0, radius_m * 1.25))
    excluded = _WALK_EXCLUDED if mode == "walk" else _DRIVE_EXCLUDED
    excluded_pattern = "|".join(sorted(excluded))
    selections = "\n".join(
        f'  way["highway"]["highway"!~"^({excluded_pattern})$"]'
        f'(around:{radius_m},{lat:.7f},{lon:.7f});'
        for lat, lon in points
    )
    return (
        f"[out:json][timeout:{max(10, min(60, int(settings.route_timeout_seconds - 5)))}];\n"
        "(\n"
        f"{selections}\n"
        ");\n"
        "(._;>;);\n"
        "out body qt;"
    )


def _allowed_way(tags: dict[str, str], mode: RouteMode) -> bool:
    highway = tags.get("highway", "")
    if not highway:
        return False
    if mode == "walk":
        if highway in _WALK_EXCLUDED or tags.get("foot") in {"no", "private"}:
            return False
        access = tags.get("access")
        return not (access in {"no", "private"} and tags.get("foot") not in {"yes", "designated", "permissive"})

    if highway in _DRIVE_EXCLUDED:
        return False
    if tags.get("motor_vehicle") in {"no", "private"} or tags.get("vehicle") in {"no", "private"}:
        return False
    access = tags.get("access")
    return not (access in {"no", "private"} and tags.get("motor_vehicle") not in {"yes", "permissive"})


def parse_overpass_graph(payload: dict, mode: RouteMode) -> RoadGraph:
    elements = payload.get("elements")
    if not isinstance(elements, list):
        raise RouteGraphError("도로망 응답 형식이 올바르지 않습니다.")

    coordinates: dict[int, Coordinate] = {}
    ways: list[dict] = []
    for element in elements:
        if not isinstance(element, dict):
            continue
        element_type = element.get("type")
        if element_type == "node":
            try:
                coordinates[int(element["id"])] = (float(element["lat"]), float(element["lon"]))
            except (KeyError, TypeError, ValueError):
                continue
        elif element_type == "way":
            ways.append(element)

    if len(coordinates) > settings.route_max_graph_nodes:
        raise RouteGraphError("선택한 구간의 도로 데이터가 너무 큽니다. 더 가까운 장소를 선택해 주세요.")

    adjacency: Adjacency = {}
    used_nodes: set[int] = set()
    for way in ways:
        tags = way.get("tags") or {}
        if not _allowed_way(tags, mode):
            continue
        node_ids = [int(node_id) for node_id in way.get("nodes", []) if int(node_id) in coordinates]
        if len(node_ids) < 2:
            continue

        oneway = str(tags.get("oneway", "")).lower()
        if mode == "walk":
            direction = "both"
        elif oneway == "-1":
            direction = "reverse"
        elif oneway in {"yes", "1", "true"} or tags.get("junction") == "roundabout":
            direction = "forward"
        else:
            direction = "both"

        for left, right in zip(node_ids, node_ids[1:]):
            weight = haversine_m(coordinates[left], coordinates[right])
            if weight <= 0:
                continue
            used_nodes.update((left, right))
            if direction in {"forward", "both"}:
                adjacency.setdefault(left, []).append((right, weight))
            if direction in {"reverse", "both"}:
                adjacency.setdefault(right, []).append((left, weight))

    if not adjacency:
        raise RouteGraphError("주변 도로망을 구성하지 못했습니다.")

    # 길찾기에 쓰이지 않는 노드 좌표를 제거해 메모리와 최근접 탐색 비용을 줄인다.
    coordinates = {node_id: coordinates[node_id] for node_id in used_nodes}
    return RoadGraph(coordinates=coordinates, adjacency=adjacency)


def nearest_node(graph: RoadGraph, point: Coordinate) -> tuple[int, float]:
    if not graph.coordinates:
        raise RouteGraphError("도로 노드가 없습니다.")
    node_id, distance = min(
        ((node_id, haversine_m(point, coordinate)) for node_id, coordinate in graph.coordinates.items()),
        key=lambda item: item[1],
    )
    return node_id, distance


def astar(graph: RoadGraph, start_node: int, end_node: int) -> tuple[list[int], float, int]:
    """실제 OSM 도로 노드 그래프에서 A* 최단거리 탐색을 수행한다."""
    if start_node == end_node:
        return [start_node], 0.0, 1

    destination = graph.coordinates[end_node]
    frontier: list[tuple[float, float, int]] = [(0.0, 0.0, start_node)]
    came_from: dict[int, int] = {}
    best_cost: dict[int, float] = {start_node: 0.0}
    explored = 0

    while frontier:
        _, current_cost, current = heappop(frontier)
        if current_cost > best_cost.get(current, float("inf")):
            continue
        explored += 1
        if current == end_node:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path, current_cost, explored

        for neighbor, edge_cost in graph.adjacency.get(current, []):
            candidate = current_cost + edge_cost
            if candidate >= best_cost.get(neighbor, float("inf")):
                continue
            best_cost[neighbor] = candidate
            came_from[neighbor] = current
            heuristic = haversine_m(graph.coordinates[neighbor], destination)
            heappush(frontier, (candidate + heuristic, candidate, neighbor))

    raise RouteNotFoundError("선택한 두 장소를 연결하는 도로 경로를 찾지 못했습니다.")


async def _fetch_graph(start: Coordinate, end: Coordinate, mode: RouteMode, radius_m: int) -> RoadGraph:
    query = _overpass_query(start, end, mode, radius_m)
    timeout = httpx.Timeout(settings.route_timeout_seconds)
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "LocalHub-SSAFY/1.11.1 educational-routing"},
        ) as client:
            response = await client.post(settings.overpass_url, data={"data": query})
            response.raise_for_status()
            payload = response.json()
    except httpx.TimeoutException as exc:
        raise RouteGraphError("도로 데이터를 불러오는 데 시간이 오래 걸립니다. 잠시 후 다시 시도해 주세요.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise RouteGraphError("도로 데이터 서비스에 연결하지 못했습니다.") from exc
    return parse_overpass_graph(payload, mode)


def _route_coordinates(
    graph: RoadGraph,
    path: list[int],
    start: Coordinate,
    end: Coordinate,
) -> list[list[float]]:
    values: list[Coordinate] = [start]
    values.extend(graph.coordinates[node_id] for node_id in path)
    values.append(end)

    # 같은 좌표가 연속으로 들어오는 경우만 제거한다. 도로 형태는 임의로 단순화하지 않는다.
    compact: list[list[float]] = []
    for latitude, longitude in values:
        point = [round(latitude, 7), round(longitude, 7)]
        if not compact or compact[-1] != point:
            compact.append(point)
    return compact


async def find_astar_route(db: Session, payload: AStarRouteRequest) -> dict:
    if payload.start_contentid == payload.end_contentid:
        raise HTTPException(status_code=400, detail="출발지와 도착지는 서로 달라야 합니다.")

    start_location = require_location(db, payload.start_contentid)
    end_location = require_location(db, payload.end_contentid)
    if start_location.mapx is None or start_location.mapy is None:
        raise HTTPException(status_code=400, detail="출발지 좌표가 제공되지 않았습니다.")
    if end_location.mapx is None or end_location.mapy is None:
        raise HTTPException(status_code=400, detail="도착지 좌표가 제공되지 않았습니다.")

    start: Coordinate = (start_location.mapy, start_location.mapx)
    end: Coordinate = (end_location.mapy, end_location.mapx)
    direct_distance = haversine_m(start, end)
    if direct_distance > settings.route_max_distance_km * 1000:
        raise HTTPException(
            status_code=400,
            detail=f"길찾기는 직선거리 {settings.route_max_distance_km:g}km 이내 장소만 지원합니다.",
        )

    cache_key = (payload.start_contentid, payload.end_contentid, payload.mode)
    cached = _ROUTE_CACHE.get(cache_key)
    if cached and cached[0] > monotonic():
        return cached[1]

    last_error: Exception | None = None
    radii = (1800, 3000, 5000) if direct_distance >= 12_000 else (1500, 2800)
    for radius_m in radii:
        try:
            graph = await _fetch_graph(start, end, payload.mode, radius_m)
            start_node, start_snap = nearest_node(graph, start)
            end_node, end_snap = nearest_node(graph, end)
            if max(start_snap, end_snap) > settings.route_max_snap_meters:
                raise RouteNotFoundError("장소와 연결되는 도로 노드를 찾지 못했습니다.")
            path, road_distance, explored = astar(graph, start_node, end_node)
            total_distance = road_distance + start_snap + end_snap
            drive_minutes = max(1, round((total_distance / 1000) / 30.0 * 60))
            walk_minutes = max(1, round((total_distance / 1000) / 4.5 * 60))
            estimated_minutes = walk_minutes if payload.mode == "walk" else drive_minutes
            result = {
                "algorithm": "A*",
                "mode": payload.mode,
                "start": {
                    "contentid": start_location.contentid,
                    "title": start_location.title,
                    "latitude": start[0],
                    "longitude": start[1],
                },
                "end": {
                    "contentid": end_location.contentid,
                    "title": end_location.title,
                    "latitude": end[0],
                    "longitude": end[1],
                },
                "distance_m": round(total_distance),
                "direct_distance_m": round(direct_distance),
                "estimated_minutes": estimated_minutes,
                "drive_minutes": drive_minutes,
                "walk_minutes": walk_minutes,
                "explored_nodes": explored,
                "coordinates": _route_coordinates(graph, path, start, end),
                "attribution": "도로 데이터 © OpenStreetMap contributors",
                "notice": "예상 경로이며 실시간 교통·공사·통행 제한은 반영하지 않습니다.",
            }
            now = monotonic()
            expired = [key for key, value in _ROUTE_CACHE.items() if value[0] <= now]
            for key in expired:
                _ROUTE_CACHE.pop(key, None)
            if len(_ROUTE_CACHE) >= _CACHE_MAX_ITEMS:
                oldest_key = min(_ROUTE_CACHE, key=lambda key: _ROUTE_CACHE[key][0])
                _ROUTE_CACHE.pop(oldest_key, None)
            _ROUTE_CACHE[cache_key] = (now + _CACHE_SECONDS, result)
            return result
        except (RouteGraphError, RouteNotFoundError) as exc:
            last_error = exc

    raise HTTPException(
        status_code=503,
        detail=str(last_error or "선택한 두 장소의 경로를 계산하지 못했습니다."),
    )
