"""
Setup script for the picarx ROS 2 package.

This script configures the installation of the picarx package, including Python modules,
launch files, configuration files, and entry points for ROS 2 nodes. It is designed for
use with the SunFounder PiCarX robot on Raspberry Pi OS (Pi 5) and Robot Hat v4.
"""

import glob
from setuptools import setup, find_packages

PACKAGE_NAME = "picarx"

setup(
    name=PACKAGE_NAME,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + PACKAGE_NAME]),
        ("share/" + PACKAGE_NAME, ["package.xml"]),
        ("share/" + PACKAGE_NAME + "/launch", glob.glob("launch/*.launch.py")),
        ("share/" + PACKAGE_NAME + "/config", glob.glob("config/*.yaml")),
    ],
    install_requires=[
        "setuptools",
        "rclpy",
        "gpiozero",
        "ackermann_msgs",
        "std_msgs",
        "sparkfun-qwiic-icm20948",
    ],
    zip_safe=True,
    maintainer="Geoffrey Zub",
    maintainer_email="gzub@alum.wpi.edu",
    description="ROS 2 package for handling speed and angle commands and publishing robot status.",
    license="Apache 2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "picarx_ackermann = picarx.picarx_ackermann_node:main",
            "picarx_ultrasonic = picarx.picarx_ultrasonic_node:main",
            "picarx_joystick = picarx.picarx_joystick_node:main",
            "picarx_grayscale = picarx.picarx_grayscale_node:main",
            "picarx_sysinfo = picarx.picarx_sysinfo_node:main",
            "picarx_detections = picarx.picarx_detections_node:main",
            "object_avoidance = picarx.object_avoidance:main",
            "picarx_pantilt = picarx.picarx_pantilt_node:main",
            "icm20948_node = picarx.icm20948_node:main",
        ],
    },
)
