#!/usr/bin/env python3
"""
Relay de /cmd_vel: repassa mensagens com QoS RELIABLE (compatível com o plugin
diff_drive do TurtleBot3 no Gazebo). Use como ponte se o teleop e o plugin não
estiverem se conectando.

Requer: source /opt/ros/humble/setup.bash
"""
import rclpy
from rclpy.qos import QoSProfile
from geometry_msgs.msg import Twist


def main():
    rclpy.init()
    node = rclpy.create_node('cmd_vel_relay')

    qos = QoSProfile(depth=10)

    pub = node.create_publisher(Twist, 'cmd_vel', qos)
    sub = node.create_subscription(
        Twist,
        'cmd_vel',
        lambda msg: pub.publish(msg),
        qos,
    )

    node.get_logger().info(
        'Relay rodando: repassa /cmd_vel (RELIABLE). '
        'Mantenha o teleop_keyboard no outro terminal.'
    )

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
