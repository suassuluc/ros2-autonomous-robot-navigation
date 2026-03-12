#!/usr/bin/env python3
"""
Mixer de cmd_vel: escolhe entre teleop (ou navigator) e obstacle_avoider.

Assina: cmd_vel_teleop, cmd_vel_avoider, obstacle_detected.
Quando obstacle_detected é True, repubblica cmd_vel_avoider em cmd_vel;
caso contrário, repubblica cmd_vel_teleop em cmd_vel.

Uso: avoider publica em cmd_vel_avoider; teleop com remap publica em cmd_vel_teleop.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool


class CmdVelMixerNode(Node):
    """Republica cmd_vel_avoider ou cmd_vel_teleop em cmd_vel conforme obstacle_detected."""

    def __init__(self):
        super().__init__('cmd_vel_mixer')
        self._obstacle_detected = False
        self._last_teleop = Twist()
        self._last_avoider = Twist()

        self._pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self._sub_teleop = self.create_subscription(
            Twist, 'cmd_vel_teleop', self._cb_teleop, 10
        )
        self._sub_avoider = self.create_subscription(
            Twist, 'cmd_vel_avoider', self._cb_avoider, 10
        )
        self._sub_obstacle = self.create_subscription(
            Bool, 'obstacle_detected', self._cb_obstacle, 10
        )
        self._timer = self.create_timer(0.05, self._publish_cmd)
        self.get_logger().info('cmd_vel_mixer: obstacle_detected -> avoider, else -> teleop')

    def _cb_teleop(self, msg: Twist) -> None:
        self._last_teleop = msg

    def _cb_avoider(self, msg: Twist) -> None:
        self._last_avoider = msg

    def _cb_obstacle(self, msg: Bool) -> None:
        self._obstacle_detected = msg.data

    def _publish_cmd(self) -> None:
        if self._obstacle_detected:
            self._pub.publish(self._last_avoider)
        else:
            self._pub.publish(self._last_teleop)


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelMixerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
