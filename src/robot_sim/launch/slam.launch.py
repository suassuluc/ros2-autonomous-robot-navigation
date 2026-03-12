#!/usr/bin/env python3
"""
Launch do slam_toolbox para mapeamento do ambiente.

Requer: simulação TurtleBot3 no Gazebo já rodando (/scan, /odom, tf).
O usuário dirige o robô com teleop para mapear; depois pode salvar o mapa
com nav2_map_server (ver docs/SLAM.md).

Uso: ros2 launch robot_sim slam.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('robot_sim')
    slam_params = os.path.join(pkg_share, 'config', 'slam_params.yaml')
    return LaunchDescription([
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params],
        ),
    ])
