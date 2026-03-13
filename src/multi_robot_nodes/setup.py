from setuptools import setup

package_name = 'multi_robot_nodes'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ayodele Abiola Arowolo',
    maintainer_email='todo@todo.todo',
    description='Multi-robot ROS 2 nodes — Tasks 3, 4, 5',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Task 3
            'husky_hello_node = multi_robot_nodes.husky_hello_node:main',
            'tb3_hello_node = multi_robot_nodes.tb3_hello_node:main',
            'odom_to_tf_broadcaster = multi_robot_nodes.odom_to_tf_broadcaster:main',
            # Task 4
            'leader_pose_publisher = multi_robot_nodes.leader_pose_publisher:main',
            'follower_controller = multi_robot_nodes.follower_controller:main',
        ],
    },
)
