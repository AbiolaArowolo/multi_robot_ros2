import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg = get_package_share_directory('multi_robot_bringup')

    # --- Dual robot spawn (Gazebo + bridge + hello nodes) ---
    dual_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg, 'launch', 'task3_dual_spawn.launch.py')
        )
    )

    # --- Husky Nav2 (delayed 20s to let Gazebo settle) ---
    husky_nav2 = TimerAction(
        period=20.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg, 'launch', 'husky_nav2.launch.py')
            )
        )]
    )

    # --- TB3 Nav2 (delayed 25s — after Husky Nav2 starts) ---
    tb3_nav2 = TimerAction(
        period=25.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg, 'launch', 'tb3_nav2.launch.py')
            )
        )]
    )

    # --- Task 5 nodes (delayed 35s — after both Nav2 stacks up) ---
    goal_sharing = TimerAction(
        period=35.0,
        actions=[Node(
            package='multi_robot_nodes',
            executable='goal_sharing_node',
            name='goal_sharing_node',
            output='screen',
        )]
    )

    role_manager = TimerAction(
        period=35.0,
        actions=[Node(
            package='multi_robot_nodes',
            executable='role_manager_node',
            name='role_manager_node',
            output='screen',
        )]
    )

    return LaunchDescription([
        dual_spawn,
        husky_nav2,
        tb3_nav2,
        goal_sharing,
        role_manager,
    ])
