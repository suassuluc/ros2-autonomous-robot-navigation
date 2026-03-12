#!/usr/bin/env python3
"""
Launch dos nós de navegação autônoma: obstacle_detector e navigator.

Requer: simulação TurtleBot3 no Gazebo já rodando (odom, scan, cmd_vel).
Uso: ros2 launch robot_sim navigation.launch.py
     ros2 launch robot_sim navigation.launch.py goal_x:=1.5 goal_y:=0.5
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('goal_x', default_value='2.0', description='Objetivo X (m)'),
        DeclareLaunchArgument('goal_y', default_value='0.0', description='Objetivo Y (m)'),

        Node(
            package='robot_sim',
            executable='obstacle_detector',
            name='obstacle_detector',
            output='screen',
        ),
        Node(
            package='robot_sim',
            executable='navigator',
            name='navigator',
            output='screen',
            parameters=[{
                'goal_x': LaunchConfiguration('goal_x'),
                'goal_y': LaunchConfiguration('goal_y'),
            }],
        ),
    ])
