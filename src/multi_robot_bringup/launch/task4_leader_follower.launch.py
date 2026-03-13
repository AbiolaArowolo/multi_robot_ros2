"""
Task 4 — Leader-Follower Launch File
=======================================
Launches:
  1. Both robots in Ignition warehouse (includes task3_dual_spawn.launch.py)
  2. leader_pose_publisher  — Husky odom → /leader/pose
  3. follower_controller    — /leader/pose + /turtlebot3/odom → /turtlebot3/cmd_vel

Usage:
  ros2 launch multi_robot_bringup task4_leader_follower.launch.py

Manual Husky driving (separate terminal):
  ros2 topic pub /a200_0000/cmd_vel geometry_msgs/msg/Twist \
    '{linear: {x: 0.3}}' --rate 10

Stop both robots:
  ros2 topic pub /a200_0000/cmd_vel geometry_msgs/msg/Twist '{}' --once
  ros2 topic pub /turtlebot3/cmd_vel geometry_msgs/msg/Twist '{}' --once
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    bringup_dir = get_package_share_directory('multi_robot_bringup')

    # ── Sub-launch: Gazebo + both robots + bridge ─────────────────────────
    dual_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, 'launch', 'task3_dual_spawn.launch.py')
        )
    )

    # ── Leader pose publisher ─────────────────────────────────────────────
    # Converts /a200_0000/odom → /leader/pose (geometry_msgs/PoseStamped)
    leader_pub = Node(
        package='multi_robot_nodes',
        executable='leader_pose_publisher',
        name='leader_pose_publisher',
        output='screen',
        emulate_tty=True,
    )

    # ── Follower controller ───────────────────────────────────────────────
    # Subscribes: /leader/pose, /turtlebot3/odom
    # Publishes:  /turtlebot3/cmd_vel
    follower_ctrl = Node(
        package='multi_robot_nodes',
        executable='follower_controller',
        name='follower_controller',
        output='screen',
        emulate_tty=True,
    )

    return LaunchDescription([
        dual_spawn,
        leader_pub,
        follower_ctrl,
    ])
