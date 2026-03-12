import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'robot_sim'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='shini',
    maintainer_email='suassunalucas8@gmail.com',
    description='Pacote de simulação: detecção de obstáculos, A*, PID e navegação autônoma.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'obstacle_detector = robot_sim.nodes.obstacle_detector:main',
            'navigator = robot_sim.nodes.navigator:main',
            'obstacle_avoider = robot_sim.nodes.obstacle_avoider:main',
            'cmd_vel_mixer = robot_sim.nodes.cmd_vel_mixer:main',
            'vision_node = robot_sim.nodes.vision_node:main',
            'exploration_goal = robot_sim.nodes.exploration_goal_node:main',
        ],
    },
)
