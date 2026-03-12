#!/usr/bin/env python3
"""
Launch: teleop com camada de desvio (mixer).

Sobe obstacle_detector, obstacle_avoider (publica em cmd_vel_avoider) e
cmd_vel_mixer. O mixer envia cmd_vel_avoider para cmd_vel quando há
obstáculo próximo; caso contrário envia cmd_vel_teleop.

O usuário deve rodar o teleop com remap para cmd_vel_teleop:
  ros2 run turtlebot3_teleop teleop_keyboard --ros-args -r cmd_vel:=cmd_vel_teleop

Requer: simulação TurtleBot3 no Gazebo já rodando.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_sim',
            executable='obstacle_detector',
            name='obstacle_detector',
            output='screen',
        ),
        Node(
            package='robot_sim',
            executable='obstacle_avoider',
            name='obstacle_avoider',
            output='screen',
            parameters=[{'use_cmd_vel_avoider': True}],
        ),
        Node(
            package='robot_sim',
            executable='cmd_vel_mixer',
            name='cmd_vel_mixer',
            output='screen',
        ),
    ])
