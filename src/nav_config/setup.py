from setuptools import setup
import os
from glob import glob

package_name = 'nav_config'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='abiola',
    maintainer_email='abayo83@gmail.com',
    description='Nav config',
    license='MIT',
    entry_points={'console_scripts': []},
)
