from setuptools import find_packages, setup

package_name = 'my_robot_pkg'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Adesanya',
    maintainer_email='you@example.com',
    description='ROS 2 publisher/subscriber and service/client examples',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'simple_talker        = my_robot_pkg.simple_talker:main',
            'simple_listener      = my_robot_pkg.simple_listener:main',
            'add_two_ints_server  = my_robot_pkg.add_two_ints_server:main',
            'add_two_ints_client  = my_robot_pkg.add_two_ints_client:main',
        ],
    },
)
