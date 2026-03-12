#!/usr/bin/env python3
"""
Launch do mundo TurtleBot3 com spawn atrasado.

O mundo turtlebot3_world demora para carregar; o spawn_entity do pacote
oficial roda junto e o serviço /spawn_entity ainda não está disponível
("Was Gazebo started with GazeboRosFactory?"). Este launch espera alguns
segundos antes de chamar o spawn, dando tempo ao gzserver de carregar
o mundo e o plugin da factory.

Uso (igual ao oficial):
  export TURTLEBOT3_MODEL=burger
  ros2 launch robot_sim turtlebot3_world_delayed.launch.py

  ros2 launch robot_sim turtlebot3_world_delayed.launch.py x_pose:=0.0 y_pose:=0.0

Com o modelo da casa (opcional):
  ros2 launch robot_sim turtlebot3_world_delayed.launch.py spawn_house:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    pkg_turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='-2.0')
    y_pose = LaunchConfiguration('y_pose', default='-0.5')
    spawn_house = LaunchConfiguration('spawn_house', default='false')

    world = os.path.join(pkg_turtlebot3_gazebo, 'worlds', 'turtlebot3_world.world')

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world}.items()
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        )
    )

    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_turtlebot3_gazebo, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # Spawn do TurtleBot3 (modelo vem de TURTLEBOT3_MODEL)
    model = os.environ.get('TURTLEBOT3_MODEL', 'burger')
    model_sdf = os.path.join(
        pkg_turtlebot3_gazebo,
        'models',
        f'turtlebot3_{model}',
        'model.sdf'
    )
    spawn_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', model,
            '-file', model_sdf,
            '-x', x_pose,
            '-y', y_pose,
            '-z', '0.01',
        ],
        output='screen',
    )
    # Atraso para o gzserver carregar o mundo e expor /spawn_entity
    spawn_delayed = TimerAction(period=12.0, actions=[spawn_node])

    # Spawn opcional do modelo da casa (turtlebot3_house) no mundo
    house_sdf = os.path.join(
        pkg_turtlebot3_gazebo, 'models', 'turtlebot3_house', 'model.sdf'
    )
    spawn_house_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'turtlebot3_house',
            '-file', house_sdf,
            '-x', '2.0',
            '-y', '0.0',
            '-z', '0.0',
        ],
        output='screen',
    )
    spawn_house_delayed = TimerAction(
        period=15.0,
        actions=[spawn_house_node],
        condition=IfCondition(
            PythonExpression(["'", spawn_house, "' == 'true'"])
        ),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('x_pose', default_value='-2.0'),
        DeclareLaunchArgument('y_pose', default_value='-0.5'),
        DeclareLaunchArgument(
            'spawn_house',
            default_value='false',
            description='Se true, spawna o modelo da casa (turtlebot3_house) no mundo',
        ),
        gzserver_cmd,
        gzclient_cmd,
        robot_state_publisher_cmd,
        spawn_delayed,
        spawn_house_delayed,
    ])
