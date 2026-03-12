#!/usr/bin/env python3
"""
Nó de navegação autônoma: planeja rota (A*) e segue waypoints com PID.

Assina /odom, /scan e opcionalmente /goal (Point). Publica /cmd_vel.
Usa grid local a partir de /scan, A* para planejar e controlador PID para seguir.
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Twist, Point
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool

from robot_sim.pid_controller import PIDController
from robot_sim.astar import astar, grid_to_world, world_to_grid, nearest_reachable_cell
from robot_sim.grid_builder import scan_to_grid


class NavigatorNode(Node):
    """Navega até um objetivo usando A* e PID."""

    def __init__(self):
        super().__init__('navigator')

        self.declare_parameter('goal_x', 2.0)
        self.declare_parameter('goal_y', 0.0)
        self.declare_parameter('grid_resolution', 0.05)
        self.declare_parameter('grid_size_m', 4.0)
        self.declare_parameter('obstacle_stop_distance', 0.35)
        self.declare_parameter('control_period', 0.1)
        self.declare_parameter('direct_goal_when_astar_fails', True)
        self.declare_parameter('replan_when_obstacle_sec', 2.5)

        self._goal_x = float(self.get_parameter('goal_x').value)
        self._goal_y = float(self.get_parameter('goal_y').value)
        self._grid_resolution = self.get_parameter('grid_resolution').value
        self._grid_size_m = self.get_parameter('grid_size_m').value
        self._obstacle_stop_distance = self.get_parameter('obstacle_stop_distance').value
        self._control_period = self.get_parameter('control_period').value
        self._direct_goal_fallback = self.get_parameter('direct_goal_when_astar_fails').value
        replan_sec = self.get_parameter('replan_when_obstacle_sec').value
        self._replan_when_obstacle_sec = float(replan_sec)

        self._odom = None
        self._scan = None
        self._waypoints: list[tuple[float, float]] = []
        self._waypoint_index = 0
        self._plan_pose = None  # (x, y, theta) quando planejamos
        self._pid = PIDController(
            kp_linear=0.5,
            kp_angular=1.2,
            max_linear=0.22,
            max_angular=1.5,
            linear_tolerance=0.12,
        )

        self._pub_cmd = self.create_publisher(Twist, 'cmd_vel', 10)
        self._sub_odom = self.create_subscription(Odometry, 'odom', self._cb_odom, 10)
        self._sub_scan = self.create_subscription(LaserScan, 'scan', self._cb_scan, 10)
        # QoS best_effort para /goal: aceita mensagens do "ros2 topic pub" (evita perda por QoS)
        qos_goal = QoSProfile(
            depth=10, reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
        )
        self._sub_goal = self.create_subscription(Point, 'goal', self._cb_goal, qos_goal)
        self._sub_obstacle = self.create_subscription(
            Bool, 'obstacle_detected', self._cb_obstacle, 10
        )

        self._obstacle_detected = False
        self._obstacle_from_scan = False  # fallback se obstacle_detector não rodar
        self._replan_requested = False  # True quando /goal chega; replaneja no control_loop
        self._last_astar_fail_log = 0.0  # throttle do aviso "A* não encontrou caminho"
        self._last_obstacle_replan = 0.0  # throttle do replan por obstáculo no caminho
        self._last_plan_skip_log = 0.0  # throttle do aviso "aguardando odom/scan"
        self._timer = self.create_timer(self._control_period, self._control_loop)
        # Forçar plano após 1.5 s (reinício do launch; dá tempo de /odom e /scan)
        self._startup_replan_timer = self.create_timer(1.5, self._on_startup_replan)

        self.get_logger().info(
            'Navigator: goal=(%.2f, %.2f), grid_res=%.2f, grid_size=%.1f m'
            % (self._goal_x, self._goal_y, self._grid_resolution, self._grid_size_m)
        )

    def _cb_odom(self, msg: Odometry) -> None:
        self._odom = msg

    def _cb_scan(self, msg: LaserScan) -> None:
        self._scan = msg

    def _cb_goal(self, msg: Point) -> None:
        self._goal_x = float(msg.x)
        self._goal_y = float(msg.y)
        self.get_logger().info(
            'Novo objetivo: (%.2f, %.2f) — replanejando.' % (self._goal_x, self._goal_y)
        )
        self._waypoints = []
        self._waypoint_index = 0
        self._replan_requested = True
        self._pid.reset_integrals()

    def _cb_obstacle(self, msg: Bool) -> None:
        self._obstacle_detected = msg.data

    def _on_startup_replan(self) -> None:
        """Uma vez após ~1.5 s: força replan se ainda não temos waypoints (reinício do launch)."""
        self._startup_replan_timer.cancel()
        if not self._waypoints:
            self.get_logger().info('Tentando planejamento inicial (após subida do nó)...')
            self._replan_requested = True
        return

    def _get_pose(self) -> tuple[float, float, float] | None:
        if self._odom is None:
            return None
        p = self._odom.pose.pose.position
        q = self._odom.pose.pose.orientation
        theta = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        return (p.x, p.y, theta)

    def _plan_once(self) -> None:
        """Monta grid a partir do scan, roda A* e preenche waypoints em odom."""
        pose = self._get_pose()
        if pose is None or self._scan is None:
            now = self.get_clock().now().nanoseconds / 1e9
            if now - self._last_plan_skip_log >= 2.0:
                self._last_plan_skip_log = now
                reason = []
                if pose is None:
                    reason.append('/odom')
                if self._scan is None:
                    reason.append('/scan')
                self.get_logger().info(
                    'Aguardando %s para replanejar (goal: %.2f, %.2f).'
                    % (' e '.join(reason), self._goal_x, self._goal_y)
                )
            return
        x, y, theta = pose

        grid, origin_x, origin_y = scan_to_grid(
            list(self._scan.ranges),
            self._scan.angle_min,
            self._scan.angle_increment,
            self._scan.range_min,
            self._scan.range_max,
            resolution=self._grid_resolution,
            grid_size_m=self._grid_size_m,
            inflation_cells=2,
        )
        rows, cols = len(grid), len(grid[0])
        num_cells = rows
        start_cell = (num_cells // 2, num_cells // 2)

        # Garantir que a célula do robô (e vizinhança) esteja livre no grid; a inflação
        # dos obstáculos pode ter coberto o centro e fazer o A* falhar sempre.
        radius_cells = max(2, int(0.3 / self._grid_resolution))  # ~0.3 m em células
        for dr in range(-radius_cells, radius_cells + 1):
            for dc in range(-radius_cells, radius_cells + 1):
                r, c = start_cell[0] + dr, start_cell[1] + dc
                if 0 <= r < rows and 0 <= c < cols:
                    grid[r][c] = 0

        # Goal em frame do robô
        gx_r = (self._goal_x - x) * math.cos(theta) + (self._goal_y - y) * math.sin(theta)
        gy_r = -(self._goal_x - x) * math.sin(theta) + (self._goal_y - y) * math.cos(theta)
        goal_cell = world_to_grid(gx_r, gy_r, origin_x, origin_y, self._grid_resolution)
        gr, gc = goal_cell
        if gr < 0 or gr >= rows or gc < 0 or gc >= cols:
            self.get_logger().warn('Objetivo fora do grid; ajustando para borda.')
            gr = max(0, min(rows - 1, gr))
            gc = max(0, min(cols - 1, gc))
            goal_cell = (gr, gc)

        # Garantir que a célula do objetivo esteja livre (pode ter sido inflada)
        if 0 <= gr < rows and 0 <= gc < cols:
            grid[gr][gc] = 0

        path = astar(grid, start_cell, goal_cell, four_connectivity=False)
        if not path:
            # Tentar objetivo alternativo: ponto livre alcançável mais próximo do objetivo original
            subgoal_cell = nearest_reachable_cell(
                grid, start_cell, goal_cell, four_connectivity=False
            )
            if subgoal_cell is not None and subgoal_cell != start_cell:
                path = astar(grid, start_cell, subgoal_cell, four_connectivity=False)
                if path:
                    self.get_logger().info(
                        'Objetivo bloqueado; indo ao ponto livre mais próximo (%.2f, %.2f).'
                        % (self._goal_x, self._goal_y)
                    )
            now = self.get_clock().now().nanoseconds / 1e9
            if not path:
                if now - self._last_astar_fail_log >= 5.0:
                    self.get_logger().warn(
                        'A* não encontrou caminho (goal=(%.2f, %.2f)). '
                        'Objetivo pode estar em obstáculo ou fora do alcance.'
                        % (self._goal_x, self._goal_y)
                    )
                    self._last_astar_fail_log = now
                if self._direct_goal_fallback:
                    self._waypoints = [(self._goal_x, self._goal_y)]
                    self._waypoint_index = 0
                    self._pid.reset_integrals()
                    self.get_logger().info(
                        'Fallback: indo direto ao objetivo (%.2f, %.2f) com PID.'
                        % (self._goal_x, self._goal_y)
                    )
                else:
                    self._waypoints = []
                    self._waypoint_index = 0
                return

        self._plan_pose = (x, y, theta)
        waypoints_odom = []
        for (row, col) in path:
            wx_r, wy_r = grid_to_world(
                row, col, origin_x, origin_y, self._grid_resolution
            )
            wx = x + wx_r * math.cos(theta) - wy_r * math.sin(theta)
            wy = y + wx_r * math.sin(theta) + wy_r * math.cos(theta)
            waypoints_odom.append((wx, wy))
        # Se o caminho tem só 1 ponto, é start=goal no grid: o waypoint vira a posição atual
        # e o robô "alcança" na hora sem publicar cmd_vel. Usar sempre o objetivo real.
        if len(waypoints_odom) <= 1:
            waypoints_odom = [(self._goal_x, self._goal_y)]
        self._waypoints = waypoints_odom
        self._waypoint_index = 0
        self._pid.reset_integrals()
        self.get_logger().info(
            'Plano com %d waypoints (objetivo: %.2f, %.2f).'
            % (len(self._waypoints), self._goal_x, self._goal_y)
        )

    def _control_loop(self) -> None:
        pose = self._get_pose()
        if pose is None:
            return
        x, y, theta = pose

        # Obstáculo perto: parar; se estávamos em rota, pedir replan (recalcular)
        if self._obstacle_detected or self._obstacle_from_scan:
            self._pub_cmd.publish(Twist())
            now = self.get_clock().now().nanoseconds / 1e9
            throttle = (now - self._last_obstacle_replan) >= self._replan_when_obstacle_sec
            if self._waypoints and throttle:
                self._last_obstacle_replan = now
                self._waypoints = []
                self._waypoint_index = 0
                self._replan_requested = True
                self.get_logger().info('Obstáculo no caminho — recalculando rota.')
            return
        if self._scan is not None:
            half_rad = math.radians(45)
            min_d = float('inf')
            for i, r in enumerate(self._scan.ranges):
                angle = self._scan.angle_min + i * self._scan.angle_increment
                in_front = -half_rad <= angle <= half_rad
                valid = self._scan.range_min <= r <= self._scan.range_max
                if in_front and valid and math.isfinite(r):
                    min_d = min(min_d, r)
            too_close = min_d != float('inf') and min_d < self._obstacle_stop_distance
            self._obstacle_from_scan = too_close

        # Replanejar quando /goal foi recebido ou quando ainda não temos waypoints
        if self._replan_requested or not self._waypoints:
            self._replan_requested = False
            self._plan_once()
            if not self._waypoints:
                return

        # Waypoint atual
        wx, wy = self._waypoints[self._waypoint_index]
        if self._pid.is_waypoint_reached(x, y, theta, wx, wy):
            self._waypoint_index += 1
            self._pid.reset_integrals()
            if self._waypoint_index >= len(self._waypoints):
                self._pub_cmd.publish(Twist())
                dist = math.hypot(self._goal_x - x, self._goal_y - y)
                self.get_logger().info(
                    'Objetivo alcançado (distância: %.2f m).' % dist
                )
                self._waypoints = []
                self._waypoint_index = 0
                return
            wx, wy = self._waypoints[self._waypoint_index]

        linear, angular = self._pid.compute(x, y, theta, wx, wy, dt=self._control_period)
        cmd = Twist()
        cmd.linear.x = float(linear)
        cmd.angular.z = float(angular)
        self._pub_cmd.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = NavigatorNode()
    # Não planejar aqui: odom/scan podem ainda não ter chegado. O control_loop
    # chama _plan_once() quando _waypoints está vazio (e já temos dados).
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
