# -*- coding: utf-8 -*-
"""Lightweight constructive heuristics for public health team routing.

This module deliberately keeps the optimization independent of QGIS so the
same planner can run with the Python versions shipped by QGIS 3 and 4.
"""


def _route_minutes(route, matrix, service_minutes, break_minutes, return_to_base):
    if not route:
        return 0.0
    total = 0.0
    previous = 0
    for stop in route:
        total += matrix[previous][stop]
        total += service_minutes[stop - 1]
        previous = stop
    if return_to_base:
        total += matrix[previous][0]
    return total + break_minutes


def _route_travel_minutes(route, matrix, return_to_base):
    if not route:
        return 0.0
    total = 0.0
    previous = 0
    for stop in route:
        total += matrix[previous][stop]
        previous = stop
    if return_to_base:
        total += matrix[previous][0]
    return total


def _best_insertion(stop, routes, matrix, service_minutes, break_minutes,
                    shift_minutes, return_to_base, balance_weight=0.0):
    best = None
    team_count = max(1, len(routes))
    target_work = shift_minutes / team_count
    for team_index, route in enumerate(routes):
        old_total = _route_minutes(
            route, matrix, service_minutes, break_minutes, return_to_base
        )
        for position in range(len(route) + 1):
            candidate = route[:position] + [stop] + route[position:]
            new_total = _route_minutes(
                candidate, matrix, service_minutes, break_minutes, return_to_base
            )
            if new_total > shift_minutes:
                continue
            added = max(0.0, new_total - old_total)
            projected = abs(new_total - target_work)
            score = added + balance_weight * projected
            if best is None or score < best[0]:
                best = (score, team_index, position, candidate, new_total)
    return best


def _two_opt(route, matrix, service_minutes, break_minutes, shift_minutes,
             return_to_base):
    """Improve a route by 2-opt while retaining its time feasibility."""
    route = list(route)
    improved = True
    passes = 0
    while improved and passes < 8 and len(route) > 3:
        improved = False
        passes += 1
        current_travel = _route_travel_minutes(route, matrix, return_to_base)
        for left in range(len(route) - 2):
            for right in range(left + 2, len(route)):
                candidate = route[:left] + list(reversed(route[left:right + 1])) + route[right + 1:]
                travel = _route_travel_minutes(candidate, matrix, return_to_base)
                if travel + sum(service_minutes[i - 1] for i in candidate) + break_minutes > shift_minutes:
                    continue
                if travel + 1e-9 < current_travel:
                    route = candidate
                    current_travel = travel
                    improved = True
                    break
            if improved:
                break
    return route


def plan_routes(matrix, service_minutes, rewards, team_count, shift_minutes,
                break_minutes=0.0, return_to_base=True, mode="all"):
    """Return route stop-index lists, unassigned stop indexes, and route times.

    Matrix index zero is the single depot; stop indexes are 1..N. ``all``
    attempts to assign every stop. ``coverage`` greedily chooses feasible
    visits with the highest reward per marginal work minute.
    """
    if team_count < 1:
        raise ValueError("チーム数は1以上にしてください。")
    if shift_minutes <= 0:
        raise ValueError("行動可能時間は0より大きくしてください。")
    if len(matrix) != len(service_minutes) + 1:
        raise ValueError("移動時間行列と訪問先数が一致しません。")
    if len(rewards) != len(service_minutes):
        raise ValueError("対応価値と訪問先数が一致しません。")
    if any(len(row) != len(matrix) for row in matrix):
        raise ValueError("移動時間行列が正方行列ではありません。")

    routes = [[] for _ in range(team_count)]
    unassigned = set(range(1, len(matrix)))

    if mode == "all":
        # Harder-to-place stops go first; among ties, distant stops go first.
        order = sorted(
            unassigned,
            key=lambda stop: (
                -service_minutes[stop - 1],
                -(matrix[0][stop] + (matrix[stop][0] if return_to_base else 0.0)),
                -rewards[stop - 1],
            ),
        )
        for stop in order:
            choice = _best_insertion(
                stop, routes, matrix, service_minutes, break_minutes,
                shift_minutes, return_to_base, balance_weight=0.15,
            )
            if choice is None:
                continue
            _score, team_index, _position, route, _minutes = choice
            routes[team_index] = route
            unassigned.remove(stop)
    elif mode == "coverage":
        while unassigned:
            best = None
            for stop in unassigned:
                choice = _best_insertion(
                    stop, routes, matrix, service_minutes, break_minutes,
                    shift_minutes, return_to_base,
                )
                if choice is None:
                    continue
                _score, team_index, position, route, new_minutes = choice
                old_minutes = _route_minutes(
                    routes[team_index], matrix, service_minutes,
                    break_minutes, return_to_base,
                )
                marginal = max(new_minutes - old_minutes, 0.1)
                value = rewards[stop - 1] / marginal
                candidate = (value, rewards[stop - 1], -marginal,
                             stop, team_index, position, route)
                if best is None or candidate[:3] > best[:3]:
                    best = candidate
            if best is None:
                break
            _value, _reward, _marginal, stop, team_index, _position, route = best
            routes[team_index] = route
            unassigned.remove(stop)
    else:
        raise ValueError("未対応の巡回計画モードです。")

    for index, route in enumerate(routes):
        routes[index] = _two_opt(
            route, matrix, service_minutes, break_minutes,
            shift_minutes, return_to_base,
        )

    route_minutes = [
        _route_minutes(route, matrix, service_minutes, break_minutes, return_to_base)
        for route in routes
    ]
    return routes, sorted(unassigned), route_minutes
