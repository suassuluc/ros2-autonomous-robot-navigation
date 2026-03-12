"""
Controlador PID para seguir waypoints.

Dado pose atual (x, y, theta) e waypoint alvo (x, y), calcula Twist
(linear.x, angular.z) para reduzir erro de distância e de ângulo.
"""

import math


class PIDController:
    """PID para velocidade linear e angular em navegação até um waypoint."""

    def __init__(
        self,
        kp_linear=0.5,
        ki_linear=0.0,
        kd_linear=0.0,
        kp_angular=1.0,
        ki_angular=0.0,
        kd_angular=0.0,
        max_linear=0.26,
        max_angular=1.82,
        linear_tolerance=0.15,
        angular_tolerance=0.1,
    ):
        self.kp_linear = kp_linear
        self.ki_linear = ki_linear
        self.kd_linear = kd_linear
        self.kp_angular = kp_angular
        self.ki_angular = ki_angular
        self.kd_angular = kd_angular
        self.max_linear = max_linear
        self.max_angular = max_angular
        self.linear_tolerance = linear_tolerance
        self.angular_tolerance = angular_tolerance

        self._error_linear_integral = 0.0
        self._error_linear_prev = 0.0
        self._error_angular_integral = 0.0
        self._error_angular_prev = 0.0

    def _normalize_angle(self, angle: float) -> float:
        """Coloca ângulo no intervalo [-pi, pi]."""
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

    def compute(
        self,
        x: float,
        y: float,
        theta: float,
        goal_x: float,
        goal_y: float,
        dt: float = 0.1,
    ) -> tuple[float, float]:
        """
        Calculate linear and angular velocity to reach (goal_x, goal_y).

        Returns
        -------
            (linear.x, angular.z) com valores limitados.

        """
        dx = goal_x - x
        dy = goal_y - y
        distance = math.hypot(dx, dy)

        # Erro angular: ângulo até o goal no frame do robô
        target_angle = math.atan2(dy, dx)
        error_angular = self._normalize_angle(target_angle - theta)

        # Erro linear = distância
        error_linear = distance

        if dt <= 0:
            dt = 0.1

        # PID angular
        self._error_angular_integral += error_angular * dt
        self._error_angular_integral = max(
            -1.0, min(1.0, self._error_angular_integral)
        )
        derivative_angular = (error_angular - self._error_angular_prev) / dt
        self._error_angular_prev = error_angular
        cmd_angular = (
            self.kp_angular * error_angular
            + self.ki_angular * self._error_angular_integral
            + self.kd_angular * derivative_angular
        )
        cmd_angular = max(-self.max_angular, min(self.max_angular, cmd_angular))

        # PID linear (só avança se estiver mais ou menos alinhado)
        self._error_linear_integral += error_linear * dt
        self._error_linear_integral = max(
            -0.5, min(0.5, self._error_linear_integral)
        )
        derivative_linear = (error_linear - self._error_linear_prev) / dt
        self._error_linear_prev = error_linear
        cmd_linear = (
            self.kp_linear * error_linear
            + self.ki_linear * self._error_linear_integral
            + self.kd_linear * derivative_linear
        )
        # Reduz velocidade linear se o ângulo estiver muito errado
        if abs(error_angular) > 0.5:
            cmd_linear *= 0.3
        cmd_linear = max(0.0, min(self.max_linear, cmd_linear))

        return (cmd_linear, cmd_angular)

    def is_waypoint_reached(
        self,
        x: float,
        y: float,
        theta: float,
        goal_x: float,
        goal_y: float,
    ) -> bool:
        """Return True if robot is within tolerance of the waypoint."""
        dx = goal_x - x
        dy = goal_y - y
        distance = math.hypot(dx, dy)
        target_angle = math.atan2(dy, dx)
        error_angular = abs(self._normalize_angle(target_angle - theta))
        return (
            distance <= self.linear_tolerance
            or error_angular <= self.angular_tolerance
            and distance <= self.linear_tolerance * 2
        )

    def reset_integrals(self) -> None:
        """Zera integrais e derivadas anteriores (útil ao trocar de waypoint)."""
        self._error_linear_integral = 0.0
        self._error_linear_prev = 0.0
        self._error_angular_integral = 0.0
        self._error_angular_prev = 0.0
