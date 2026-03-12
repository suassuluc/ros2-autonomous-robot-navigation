#!/usr/bin/env python3
"""
Nó de "ciclo de movimento": publica objetivos aleatórios em /goal a cada intervalo.

Objetivo: dar autonomia aparente ao robô — em vez de repetir a mesma rota, ele
recebe um novo objetivo a cada N minutos (ex.: 2 min), tende a ir até lá
(com o obstacle_avoider com use_goal:=true) e desvia de obstáculos. Em ~20 min
o robô passa por várias rotas diferentes e percorre mais o mapa.

Modos:
- use_relative_goals=True (padrão): objetivo = posição atual + distância
  aleatória em direção aleatória (1.5 a 4 m). Favorece exploração contínua.
- use_relative_goals=False: objetivo = ponto aleatório dentro de um retângulo
  (goal_x_min/max, goal_y_min/max). Bom para mapa conhecido (ex.: turtlebot3_world).
"""

import math
import random
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from nav_msgs.msg import Odometry


class ExplorationGoalNode(Node):
    """Publica um novo objetivo aleatório em /goal a cada goal_interval_sec."""

    def __init__(self):
        super().__init__('exploration_goal')

        self.declare_parameter('goal_interval_sec', 120.0)  # novo objetivo a cada 2 min → ~10 rotas em 20 min
        self.declare_parameter('use_relative_goals', True)
        self.declare_parameter('relative_min_dist', 1.5)
        self.declare_parameter('relative_max_dist', 4.0)
        self.declare_parameter('goal_x_min', -2.5)
        self.declare_parameter('goal_x_max', 2.5)
        self.declare_parameter('goal_y_min', -2.5)
        self.declare_parameter('goal_y_max', 2.5)
        self.declare_parameter('publish_immediately', True)  # publicar um goal ao subir

        def _float_param(name: str, default: float) -> float:
            v = self.get_parameter(name).value
            return float(v) if v is not None else default

        self._interval = _float_param('goal_interval_sec', 120.0)
        self._use_relative = self.get_parameter('use_relative_goals').value in (True, 'true', '1')
        self._rel_min = _float_param('relative_min_dist', 1.5)
        self._rel_max = _float_param('relative_max_dist', 4.0)
        self._x_min = _float_param('goal_x_min', -2.5)
        self._x_max = _float_param('goal_x_max', 2.5)
        self._y_min = _float_param('goal_y_min', -2.5)
        self._y_max = _float_param('goal_y_max', 2.5)
        self._publish_immediately = self.get_parameter('publish_immediately').value in (True, 'true', '1')

        self._pub_goal = self.create_publisher(Point, 'goal', 10)
        self._sub_odom = self.create_subscription(Odometry, 'odom', self._cb_odom, 10)

        self._odom_x: float = 0.0
        self._odom_y: float = 0.0
        self._have_odom = False

        self._timer = self.create_timer(self._interval, self._publish_goal)
        if self._publish_immediately:
            self._start_timer = self.create_timer(2.0, self._publish_first_goal)

        self.get_logger().info(
            'Exploration goal: novo objetivo a cada %.0f s, relative=%s'
            % (self._interval, self._use_relative)
        )

    def _cb_odom(self, msg: Odometry) -> None:
        self._odom_x = msg.pose.pose.position.x
        self._odom_y = msg.pose.pose.position.y
        self._have_odom = True

    def _publish_first_goal(self) -> None:
        self._start_timer.cancel()
        self._publish_goal()

    def _publish_goal(self) -> None:
        if self._use_relative and self._have_odom:
            dist = random.uniform(self._rel_min, self._rel_max)
            angle = random.uniform(0, 2 * math.pi)
            gx = self._odom_x + dist * math.cos(angle)
            gy = self._odom_y + dist * math.sin(angle)
            # Limitar ao retângulo para não fugir do mapa
            gx = max(self._x_min, min(self._x_max, gx))
            gy = max(self._y_min, min(self._y_max, gy))
        else:
            gx = random.uniform(self._x_min, self._x_max)
            gy = random.uniform(self._y_min, self._y_max)

        msg = Point()
        msg.x = float(gx)
        msg.y = float(gy)
        msg.z = 0.0
        self._pub_goal.publish(msg)
        self.get_logger().info(
            'Novo objetivo de exploração: (%.2f, %.2f)' % (msg.x, msg.y)
        )


def main(args=None):
    rclpy.init(args=args)
    node = ExplorationGoalNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
