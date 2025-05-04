import glob
from setuptools import setup, find_packages
import os

package_name = "picarx"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.launch.py'))  # Corrected launch file installation
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Your Name",
    maintainer_email="your_email@example.com",  # Replace with a valid email
    description="ROS 2 package for handling speed and angle commands and publishing robot status.",
    license="Apache 2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "picarx_ackermann = picarx.picarx_ackermann_node:main",  # ROS 2 node entry point
            "picarx_ultrasonic = picarx.picarx_ultrasonic_node:main",  # ROS 2 node entry point
        ],
    },
)
