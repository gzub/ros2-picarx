"""
Setup script for the object_avoidance ROS 2 package.

This script configures the installation of the object_avoidance package,
including Python modules, launch files, and entry points for ROS 2 nodes.
"""

import glob
from setuptools import find_packages, setup

PACKAGE_NAME = "object_avoidance"

setup(
    name=PACKAGE_NAME,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + PACKAGE_NAME]),
        ("share/" + PACKAGE_NAME, ["package.xml"]),
        (
            "share/" + PACKAGE_NAME + "/launch",
            glob.glob("launch/*.launch.py"),
        ),  # Corrected launch file installation
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="gzub",
    maintainer_email="gzub@todo.todo",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "object_avoidance = object_avoidance.object_avoidance:main"  # ROS 2 node entry point
        ],
    },
)
