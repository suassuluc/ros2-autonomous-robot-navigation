#!/usr/bin/env python3
"""
Launch do nó de desvio automático de obstáculos (só avoider).

O robô recebe cmd_vel apenas do obstacle_avoider e desvia de obstáculos
sem objetivo fixo (ou com objetivo se use_goal:=true e /goal for publicado).

Requer: simulação TurtleBot3 no Gazebo já rodando.
Uso: ros2 launch robot_sim avoider.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_sim',
            executable='obstacle_avoider',
            name='obstacle_avoider',
            output='screen',
            parameters=[{'use_cmd_vel_avoider': False}],
        ),
    ])
