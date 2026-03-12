#!/usr/bin/env python3
"""
Launch do nó de visão (seguimento de cor).

Requer: fonte de imagem no tópico de câmera (ex.: TurtleBot3 waffle_pi no Gazebo
ou ros2 run usb_cam usb_cam_node_exe). Por padrão usa camera/image_raw.

Uso: ros2 launch robot_sim vision.launch.py
     ros2 launch robot_sim vision.launch.py image_topic:=/camera/image_raw
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'image_topic',
            default_value='camera/image_raw',
            description='Tópico da imagem (sensor_msgs/Image)',
        ),
        DeclareLaunchArgument(
            'publish_cmd_vel',
            default_value='true',
            description='Publicar cmd_vel para seguir o alvo',
        ),
        Node(
            package='robot_sim',
            executable='vision_node',
            name='vision_node',
            output='screen',
            parameters=[{
                'image_topic': LaunchConfiguration('image_topic'),
                'publish_cmd_vel': LaunchConfiguration('publish_cmd_vel'),
            }],
        ),
    ])
