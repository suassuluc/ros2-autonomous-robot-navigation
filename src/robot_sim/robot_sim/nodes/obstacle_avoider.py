#!/usr/bin/env python3
"""
Nó de desvio automático de obstáculos a partir do LaserScan.

Usa setores (esquerda, centro, direita) para decidir direção: se o centro
está bloqueado, gira para o lado mais livre e avança com velocidade reduzida.
Pode opcionalmente assinar um objetivo (Point) para tender naquela direção.

Publica em cmd_vel (ou em cmd_vel_avoider se use_cmd_vel_avoider=True)
para integração com mixer (teleop/navigator + avoider).
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist, Point
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool


class ObstacleAvoiderNode(Node):
    """Desvia de obstáculos usando setores do scan (esquerda/centro/direita)."""

    def __init__(self):
        super().__init__('obstacle_avoider')

        self.declare_parameter('min_safe_distance', 0.45)
        self.declare_parameter('sector_angle_deg', 45.0)  # ±graus por setor (centro = 2*sector)
        self.declare_parameter('max_linear', 0.22)
        self.declare_parameter('max_angular', 1.2)
        self.declare_parameter('use_goal', False)  # se True, assina /goal e tende na direção
        self.declare_parameter('use_cmd_vel_avoider', False)  # publica em cmd_vel_avoider para mixer
        self.declare_parameter('control_period', 0.05)

        self._min_safe = self.get_parameter('min_safe_distance').value
        self._sector_deg = self.get_parameter('sector_angle_deg').value
        self._max_linear = self.get_parameter('max_linear').value
        self._max_angular = self.get_parameter('max_angular').value
        self._use_goal = self.get_parameter('use_goal').value
        self._use_avoider_topic = self.get_parameter('use_cmd_vel_avoider').value
        period = self.get_parameter('control_period').value

        topic_out = 'cmd_vel_avoider' if self._use_avoider_topic else 'cmd_vel'
        self._pub_cmd = self.create_publisher(Twist, topic_out, 10)
        self._sub_scan = self.create_subscription(
            LaserScan, 'scan', self._cb_scan, 10
        )
        if self._use_goal:
            self._sub_goal = self.create_subscription(
                Point, 'goal', self._cb_goal, 10
            )
        else:
            self._sub_goal = None

        self._scan = None
        self._goal_x: float | None = None
        self._goal_y: float | None = None
        self._odom_x: float = 0.0
        self._odom_y: float = 0.0
        self._odom_theta: float = 0.0
        self._have_odom = False
        self._sub_odom = self.create_subscription(
            Odometry, 'odom', self._cb_odom, 10
        )

        self._timer = self.create_timer(period, self._control_loop)
        self.get_logger().info(
            'Obstacle avoider: min_safe=%.2f m, sector=%.0f deg, out=%s'
            % (self._min_safe, self._sector_deg, topic_out)
        )

    def _cb_odom(self, msg) -> None:
        self._odom_x = msg.pose.pose.position.x
        self._odom_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self._odom_theta = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        self._have_odom = True

    def _cb_scan(self, msg: LaserScan) -> None:
        self._scan = msg

    def _cb_goal(self, msg: Point) -> None:
        self._goal_x = float(msg.x)
        self._goal_y = float(msg.y)

    def _sector_min_distances(self) -> tuple[float, float, float]:
        """Retorna (min_esq, min_centro, min_dir) em metros."""
        if self._scan is None:
            return (float('inf'), float('inf'), float('inf'))
        angle_min = self._scan.angle_min
        angle_inc = self._scan.angle_increment
        ranges = list(self._scan.ranges)
        rmin = self._scan.range_min
        rmax = self._scan.range_max
        half = math.radians(self._sector_deg)
        min_l, min_c, min_r = float('inf'), float('inf'), float('inf')
        for i, r in enumerate(ranges):
            if not (rmin <= r <= rmax) or not math.isfinite(r):
                continue
            angle = angle_min + i * angle_inc
            if -half <= angle <= half:
                min_c = min(min_c, r)
            elif angle < -half:
                min_l = min(min_l, r)
            else:
                min_r = min(min_r, r)
        return (min_l, min_c, min_r)

    def _control_loop(self) -> None:
        min_l, min_c, min_r = self._sector_min_distances()
        cmd = Twist()

        # Centro livre o suficiente: ir em frente (com possível correção para o goal)
        if min_c >= self._min_safe:
            linear = self._max_linear * 0.8
            angular = 0.0
            if self._use_goal and self._goal_x is not None and self._goal_y is not None and self._have_odom:
                dx = self._goal_x - self._odom_x
                dy = self._goal_y - self._odom_y
                goal_angle = math.atan2(dy, dx)
                err = goal_angle - self._odom_theta
                while err > math.pi:
                    err -= 2 * math.pi
                while err < -math.pi:
                    err += 2 * math.pi
                angular = max(-self._max_angular, min(self._max_angular, err * 0.5))
            cmd.linear.x = float(linear)
            cmd.angular.z = float(angular)
            self._pub_cmd.publish(cmd)
            return

        # Centro bloqueado: girar para o lado mais livre e avançar devagar
        if min_l > min_r:
            # Esquerda mais livre
            angular = self._max_angular * 0.7
            linear = self._max_linear * 0.15 if min_l > self._min_safe * 0.8 else 0.0
        else:
            angular = -self._max_angular * 0.7
            linear = self._max_linear * 0.15 if min_r > self._min_safe * 0.8 else 0.0
        cmd.linear.x = float(linear)
        cmd.angular.z = float(angular)
        self._pub_cmd.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoiderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._pub_cmd.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
