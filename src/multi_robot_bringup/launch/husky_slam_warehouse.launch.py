#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory('clearpath_gz'),
            '/launch/simulation.launch.py'
        ]),
        launch_arguments={'world': 'warehouse'}.items()
    )

    # Bridge /a200_0000/tf → /tf so SLAM can see TF frames
    tf_bridge = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='topic_tools',
                executable='relay',
                name='tf_relay',
                arguments=['/a200_0000/tf', '/tf'],
                output='screen'
            ),
            Node(
                package='topic_tools',
                executable='relay',
                name='tf_static_relay',
                arguments=['/a200_0000/tf_static', '/tf_static'],
                output='screen'
            )
        ]
    )

    slam = TimerAction(
        period=12.0,
        actions=[
            Node(
                package='slam_toolbox',
                executable='async_slam_toolbox_node',
                name='slam_toolbox',
                output='screen',
                parameters=[
                    os.path.join(
                        get_package_share_directory('nav_config'),
                        'husky_slam_params.yaml'
                    )
                ],
                remappings=[
                    ('scan', '/a200_0000/sensors/lidar2d_0/scan')
                ]
            )
        ]
    )

    return LaunchDescription([
        gazebo,
        tf_bridge,
        slam
    ])
