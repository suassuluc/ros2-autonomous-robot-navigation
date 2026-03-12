"""
Planejamento de caminho A* em grid 2D.

Entrada: grid (ocupado/livre), célula inicial, célula objetivo.
Saída: lista de células do caminho (ou vazia se não houver caminho).
"""

import heapq
from collections import deque
from typing import List, Tuple


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Distância Euclidiana entre duas células (admissível para A*)."""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def astar(
    grid: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    four_connectivity: bool = False,
) -> List[Tuple[int, int]]:
    """
    Compute shortest path on 2D grid using A*.

    Args:
        grid: matriz 2D; 0 = livre, 1 (ou !=0) = ocupado.
        start: (row, col) inicial.
        goal: (row, col) objetivo.
        four_connectivity: True = 4 vizinhos (cima, baixo, esq, dir);
                          False = 8 vizinhos (inclui diagonais).

    Returns
    -------
        Lista de (row, col) do start ao goal (inclusive), ou [] se não houver caminho.

    """
    if not grid or not grid[0]:
        return []

    rows = len(grid)
    cols = len(grid[0])

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols

    def is_free(r: int, c: int) -> bool:
        return in_bounds(r, c) and grid[r][c] == 0

    if not is_free(start[0], start[1]) or not is_free(goal[0], goal[1]):
        return []

    # (f, g, (r, c)); f = g + h
    # open_set: heap por f
    open_set = []
    g_score = {start: 0}
    f_start = g_score[start] + heuristic(start, goal)
    heapq.heappush(open_set, (f_start, g_score[start], start))
    came_from: dict[Tuple[int, int], Tuple[int, int] | None] = {start: None}

    if four_connectivity:
        neighbors_deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    else:
        neighbors_deltas = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ]

    while open_set:
        _, g_cur, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current is not None:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for dr, dc in neighbors_deltas:
            nr, nc = current[0] + dr, current[1] + dc
            neighbor = (nr, nc)
            if not is_free(nr, nc):
                continue
            # Custo 1 para cardeais, sqrt(2) para diagonais
            step_cost = 1.0 if dr == 0 or dc == 0 else 1.414
            tentative_g = g_cur + step_cost
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_val = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_val, tentative_g, neighbor))

    return []


def nearest_reachable_cell(
    grid: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    four_connectivity: bool = False,
) -> Tuple[int, int] | None:
    """
    Find reachable free cell closest to goal (BFS from start, then min dist to goal).

    Returns
    -------
        (row, col) of that cell, or None if start is not free.

    """
    if not grid or not grid[0]:
        return None
    rows = len(grid)
    cols = len(grid[0])

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols

    def is_free(r: int, c: int) -> bool:
        return in_bounds(r, c) and grid[r][c] == 0

    if not is_free(start[0], start[1]):
        return None

    if four_connectivity:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    else:
        deltas = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ]

    reachable = set()
    queue = deque([start])
    reachable.add(start)
    while queue:
        r, c = queue.popleft()
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if (nr, nc) not in reachable and is_free(nr, nc):
                reachable.add((nr, nc))
                queue.append((nr, nc))

    if not reachable:
        return None
    best = None
    best_dist = float('inf')
    for cell in reachable:
        d = heuristic(cell, goal)
        if d < best_dist:
            best_dist = d
            best = cell
    return best


def world_to_grid(
    x: float, y: float,
    origin_x: float, origin_y: float,
    resolution: float,
) -> Tuple[int, int]:
    """Convert world coordinates (meters) to grid cell (row, col)."""
    col = int((x - origin_x) / resolution)
    row = int((y - origin_y) / resolution)
    return (row, col)


def grid_to_world(
    row: int, col: int,
    origin_x: float, origin_y: float,
    resolution: float,
) -> Tuple[float, float]:
    """Convert grid cell to world coordinates (cell center)."""
    x = origin_x + (col + 0.5) * resolution
    y = origin_y + (row + 0.5) * resolution
    return (x, y)
