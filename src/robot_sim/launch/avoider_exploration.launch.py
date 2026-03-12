#!/usr/bin/env python3
"""
Launch: desvio de obstáculos + ciclo de exploração (objetivos aleatórios).

Sobe o obstacle_avoider com use_goal:=true e o exploration_goal_node, que
publica um novo objetivo em /goal a cada N minutos (padrão 2 min). O robô
tende a ir em direção a esse objetivo e desvia de obstáculos; quando chega
o tempo, recebe outro objetivo e muda de rota. Em ~20 min o robô percorre
várias regiões do mapa em vez de repetir a mesma rota.

Uso:
  ros2 launch robot_sim avoider_exploration.launch.py
  ros2 launch robot_sim avoider_exploration.launch.py goal_interval_sec:=180
  (goal_interval_sec:=180 = novo objetivo a cada 3 min; 20 min / 3 ≈ 6–7 rotas)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'goal_interval_sec',
            default_value='120',
            description='Intervalo em segundos entre novos objetivos (ex: 120 = 2 min, ~10 rotas em 20 min)',
        ),
        DeclareLaunchArgument(
            'use_relative_goals',
            default_value='true',
            description='True = objetivo à frente em direção aleatória; False = ponto aleatório no retângulo',
        ),
        DeclareLaunchArgument(
            'relative_min_dist',
            default_value='1.5',
            description='Distância mínima (m) para objetivo relativo',
        ),
        DeclareLaunchArgument(
            'relative_max_dist',
            default_value='4.0',
            description='Distância máxima (m) para objetivo relativo',
        ),
        Node(
            package='robot_sim',
            executable='obstacle_avoider',
            name='obstacle_avoider',
            output='screen',
            parameters=[{
                'use_goal': True,
                'use_cmd_vel_avoider': False,
            }],
        ),
        Node(
            package='robot_sim',
            executable='exploration_goal',
            name='exploration_goal',
            output='screen',
            parameters=[{
                'goal_interval_sec': LaunchConfiguration('goal_interval_sec'),
                'use_relative_goals': LaunchConfiguration('use_relative_goals'),
                'relative_min_dist': LaunchConfiguration('relative_min_dist'),
                'relative_max_dist': LaunchConfiguration('relative_max_dist'),
            }],
        ),
    ])
