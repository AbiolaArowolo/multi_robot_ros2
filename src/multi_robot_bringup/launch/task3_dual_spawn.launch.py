"""
Task 3 — Unified Dual Robot Spawn (SDF approach)

Spawns TB3 from a native Ignition SDF (not URDF conversion).
The URDF is still used for robot_state_publisher TF, but the
SDF defines the actual Ignition physics model with native plugins.

Usage:
  ros2 launch multi_robot_bringup task3_dual_spawn.launch.py

Verify:
  ros2 node list | grep -E 'turtlebot3|a200_0000'
  ros2 topic pub /turtlebot3/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}}' --rate 10
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():

    pkg_share = get_package_share_directory('multi_robot_bringup')

    # ═══════════════════════════════════════════════════════════════════
    # 1. HUSKY — Ignition Gazebo warehouse world + Husky A200
    # ═══════════════════════════════════════════════════════════════════
    husky_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('clearpath_gz'),
                'launch', 'simulation.launch.py'
            )
        ),
        launch_arguments={'world': 'warehouse'}.items(),
    )

    # ═══════════════════════════════════════════════════════════════════
    # 2. TURTLEBOT3
    # ═══════════════════════════════════════════════════════════════════

    # 2a. Robot State Publisher — uses URDF for ROS TF tree
    #     (The URDF defines the link/joint structure for RViz etc.)
    urdf_file = os.path.join(
        get_package_share_directory('turtlebot3_description'),
        'urdf', 'turtlebot3_burger.urdf')
    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    tb3_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace='turtlebot3',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
        output='screen',
    )

    # 2b. Spawn TB3 into Ignition — uses native SDF for physics
    #     The SDF has Ignition-native plugins (DiffDrive, JointState, gpu_lidar)
    sdf_file = os.path.join(pkg_share, 'models', 'turtlebot3_burger',
                            'model.sdf')
    tb3_spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'turtlebot3',
            '-file', sdf_file,
            '-x', '2.0',
            '-y', '2.0',
            '-z', '0.01',
        ],
        output='screen',
    )

    # 2c. ros_gz_bridge — namespaced to /turtlebot3/
    #     Bridges Ignition topics to ROS 2 under /turtlebot3/ namespace.
    #     Uses @ for bidirectional bridges.
    tb3_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='tb3_bridge',
        namespace='turtlebot3',
        arguments=[
            '/turtlebot3/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@ignition.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan@ignition.msgs.LaserScan',
            '/joint_states@sensor_msgs/msg/JointState@ignition.msgs.Model',
            '/model/turtlebot3/tf@tf2_msgs/msg/TFMessage@ignition.msgs.Pose_V',
        ],
        remappings=[
            ('/turtlebot3/cmd_vel', '/turtlebot3/cmd_vel'),
            ('/odom', '/turtlebot3/odom'),
            ('/scan', '/turtlebot3/scan'),
            ('/joint_states', '/turtlebot3/joint_states'),
            ('/model/turtlebot3/tf', '/tf'),
        ],
        output='screen',
    )

    # 2d. odom_to_tf_broadcaster — reliable TF from odometry
    tb3_odom_tf = Node(
        package='multi_robot_nodes',
        executable='odom_to_tf_broadcaster',
        namespace='turtlebot3',
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    # ═══════════════════════════════════════════════════════════════════
    # 3. TIMING — Delay TB3 spawn to let Gazebo fully start
    # ═══════════════════════════════════════════════════════════════════
    delayed_tb3 = TimerAction(
        period=15.0,
        actions=[tb3_spawn],
    )

    # ═══════════════════════════════════════════════════════════════════
    return LaunchDescription([
        husky_sim,
        tb3_robot_state_publisher,
        tb3_bridge,
        tb3_odom_tf,
        delayed_tb3,
    ])
