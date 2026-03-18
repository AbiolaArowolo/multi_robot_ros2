import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    bringup_dir = get_package_share_directory('multi_robot_bringup')

    dual_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, 'launch', 'task3_dual_spawn.launch.py')
        )
    )

    leader_pub = Node(
        package='multi_robot_nodes',
        executable='leader_pose_publisher',
        name='leader_pose_publisher',
        output='screen',
        emulate_tty=True,
    )

    # follower_ctrl disabled — use breadcrumb_follower manually
    # follower_ctrl = Node(
    #     package='multi_robot_nodes',
    #     executable='follower_controller',
    #     name='follower_controller',
    #     output='screen',
    #     emulate_tty=True,
    # )

    return LaunchDescription([
        dual_spawn,
        leader_pub,
    ])
