"""
Construção de grid de ocupação a partir de LaserScan.

Usado pelo navigator para montar um mapa local e rodar A*.
"""

import math
from typing import List, Tuple

# Assumindo sensor_msgs.msg.LaserScan como tipo (ranges, angle_min, angle_max, angle_increment)
# Para não depender de ROS aqui nos tipos, usamos estrutura simples.


def scan_to_grid(
    ranges: list,
    angle_min: float,
    angle_increment: float,
    range_min: float,
    range_max: float,
    resolution: float = 0.05,
    grid_size_m: float = 5.0,
    inflation_cells: int = 2,
    invalid_is_obstacle: bool = False,
) -> Tuple[List[List[int]], float, float]:
    """
    Convert LaserScan (robot frame) to 2D occupancy grid.

    Robot at grid center. Robot X = forward, Y = left.

    Args:
        ranges: distâncias por ângulo (índice 0 = angle_min).
        angle_min: ângulo mínimo do scan (rad).
        angle_increment: incremento entre leituras (rad).
        range_min, range_max: limites válidos do sensor.
        resolution: tamanho da célula em metros.
        grid_size_m: metade do lado do grid em metros (grid total = 2*grid_size_m).
        inflation_cells: quantas células inflar em volta de cada obstáculo.
        invalid_is_obstacle: se True, nan/inf são tratados como obstáculo.

    Returns
    -------
        (grid, origin_x, origin_y) onde grid[row][col]: 0=livre, 1=ocupado.
        origin em metros (canto inferior esquerdo do grid no frame do robô).

    """
    num_cells = int(2.0 * grid_size_m / resolution)
    if num_cells <= 0:
        num_cells = 1
    grid = [[0] * num_cells for _ in range(num_cells)]
    origin_x = -grid_size_m
    origin_y = -grid_size_m

    num_ranges = len(ranges)
    for i in range(num_ranges):
        angle = angle_min + i * angle_increment
        r = ranges[i]
        if not (range_min <= r <= range_max) and not invalid_is_obstacle:
            continue
        if (math.isnan(r) or math.isinf(r)) and not invalid_is_obstacle:
            continue
        if math.isnan(r) or math.isinf(r):
            r = range_max
        # No frame do robô: x = frente, y = esquerda
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        col = int((x - origin_x) / resolution)
        row = int((y - origin_y) / resolution)
        if 0 <= row < num_cells and 0 <= col < num_cells:
            grid[row][col] = 1

    # Inflar obstáculos
    if inflation_cells > 0:
        obstacles = [
            (r, c) for r in range(num_cells) for c in range(num_cells)
            if grid[r][c] == 1
        ]
        for r, c in obstacles:
            for dr in range(-inflation_cells, inflation_cells + 1):
                for dc in range(-inflation_cells, inflation_cells + 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < num_cells and 0 <= nc < num_cells:
                        grid[nr][nc] = 1

    return (grid, origin_x, origin_y)
