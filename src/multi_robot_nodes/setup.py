from setuptools import find_packages, setup

package_name = 'multi_robot_nodes'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='abiola',
    maintainer_email='abayo83@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'odom_to_tf_broadcaster = multi_robot_nodes.odom_to_tf_broadcaster:main',
            'husky_hello_node = multi_robot_nodes.husky_hello_node:main',
            'tb3_hello_node = multi_robot_nodes.tb3_hello_node:main',
        ],
    },
)
