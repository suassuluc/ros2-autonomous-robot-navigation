#!/usr/bin/env python3
"""
Launch do Nav2 para navegação autônoma com mapa pré-construído.

Requer: mapa já gerado (ver docs/SLAM.md) e simulação TurtleBot3 no Gazebo.
Passa use_sim_time:=true e o arquivo de mapa para o bringup do Nav2.

Uso:
  ros2 launch robot_sim nav2.launch.py map:=/path/to/map.yaml
  ros2 launch robot_sim nav2.launch.py map:=/home/shini/ros2_ws/maps/my_map.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    robot_sim_share = get_package_share_directory('robot_sim')
    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    nav2_launch_dir = os.path.join(nav2_bringup_share, 'launch')
    params_file = os.path.join(robot_sim_share, 'config', 'nav2_params.yaml')

    default_map = os.path.expanduser('~/ros2_ws/maps/my_map.yaml')
    map_arg = DeclareLaunchArgument(
        'map',
        default_value=default_map,
        description='Caminho completo para o arquivo YAML do mapa (ex: .../maps/my_map.yaml)',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Usar tempo da simulação (Gazebo)',
    )

    bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_launch_dir, 'bringup_launch.py')),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'params_file': params_file,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'slam': 'False',
        }.items(),
    )

    return LaunchDescription([
        map_arg,
        use_sim_time_arg,
        bringup_launch,
    ])
