import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    pkg = get_package_share_directory('multi_robot_bringup')
    namespace = 'turtlebot3'

    map_yaml = os.path.join(
        os.path.expanduser('~'), 'ros2_ws', 'maps', 'husky_map.yaml'
    )
    params_file = os.path.join(pkg, 'config', 'tb3_nav2_params.yaml')

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites={'yaml_filename': map_yaml},
        convert_types=True,
    )

    return LaunchDescription([
        # Odom → TF broadcaster (tb3_base_footprint)
        Node(
            package='multi_robot_nodes',
            executable='odom_to_tf_broadcaster',
            name='odom_to_tf_broadcaster',
            namespace=namespace,
            output='screen',
            remappings=[('odom', '/turtlebot3/odom')],
        ),
        # Static TF: tb3_base_footprint → tb3_base_link (z=0.010m — wheel radius)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tb3_base_footprint_to_base_link',
            arguments=['0', '0', '0.010', '0', '0', '0',
                       'tb3_base_footprint', 'tb3_base_link'],
        ),
        # Static TF: tb3_base_link → base_scan (LiDAR mount position)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tb3_base_link_to_base_scan',
            arguments=['-0.032', '0', '0.172', '0', '0', '0',
                       'tb3_base_link', 'base_scan'],
        ),
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            namespace=namespace,
            output='screen',
            parameters=[configured_params],
        ),
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            namespace=namespace,
            output='screen',
            parameters=[configured_params],
        ),
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            namespace=namespace,
            output='screen',
            parameters=[configured_params],
        ),
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            namespace=namespace,
            output='screen',
            parameters=[configured_params],
        ),
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            namespace=namespace,
            output='screen',
            parameters=[configured_params],
        ),
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            namespace=namespace,
            output='screen',
            parameters=[configured_params],
        ),
        Node(
            package='nav2_smoother',
            executable='smoother_server',
            name='smoother_server',
            namespace=namespace,
            output='screen',
            parameters=[configured_params],
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            namespace=namespace,
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'node_names': ['map_server', 'amcl'],
            }],
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            namespace=namespace,
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'node_names': [
                    'controller_server',
                    'planner_server',
                    'behavior_server',
                    'bt_navigator',
                    'smoother_server',
                ],
            }],
        ),
    ])
