#!/usr/bin/env python3
"""
Nó de detecção de obstáculos a partir do LaserScan.

Assina /scan, publica distância mínima frontal e booleano de obstáculo próximo,
para uso pelo navigator (parar ou replanejar).
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, Float32


class ObstacleDetectorNode(Node):
    """Detecta obstáculos à frente e em setores a partir de /scan."""

    def __init__(self):
        super().__init__('obstacle_detector')

        self.declare_parameter('min_distance', 0.4)
        self.declare_parameter('front_angle_deg', 60.0)  # ±graus em relação à frente

        self._min_distance = self.get_parameter('min_distance').value
        self._front_angle_deg = self.get_parameter('front_angle_deg').value

        self._pub_min_dist = self.create_publisher(Float32, 'min_obstacle_distance', 10)
        self._pub_obstacle = self.create_publisher(Bool, 'obstacle_detected', 10)
        self._sub_scan = self.create_subscription(
            LaserScan,
            'scan',
            self._cb_scan,
            10,
        )

        self.get_logger().info(
            'Obstacle detector: min_distance=%.2f m, front_angle=%.0f deg'
            % (self._min_distance, self._front_angle_deg)
        )

    def _cb_scan(self, msg: LaserScan) -> None:
        angle_min = msg.angle_min
        angle_inc = msg.angle_increment
        ranges = list(msg.ranges)
        range_min = msg.range_min
        range_max = msg.range_max

        # Setor frontal em radianos (±front_angle_deg)
        half_rad = math.radians(self._front_angle_deg)
        min_dist = float('inf')
        for i, r in enumerate(ranges):
            angle = angle_min + i * angle_inc
            if angle < -half_rad or angle > half_rad:
                continue
            if not (range_min <= r <= range_max):
                continue
            if math.isfinite(r):
                min_dist = min(min_dist, r)

        if min_dist == float('inf'):
            min_dist = range_max

        self._pub_min_dist.publish(Float32(data=min_dist))
        self._pub_obstacle.publish(Bool(data=min_dist < self._min_distance))


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
