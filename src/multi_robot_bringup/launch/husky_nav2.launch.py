#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg = get_package_share_directory('multi_robot_bringup')
    nav2_bringup = get_package_share_directory('nav2_bringup')

    map_file = os.path.join(
        os.path.expanduser('~'), 'ros2_ws', 'maps', 'husky_map.yaml'
    )
    params_file = os.path.join(pkg, 'config', 'husky_nav2_params.yaml')

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'True',
            'map': map_file,
            'namespace': '/a200_0000',
            'params_file': params_file,
        }.items()
    )

    return LaunchDescription([nav2])
