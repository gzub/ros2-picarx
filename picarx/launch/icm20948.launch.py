"""
Launch file for the ICM20948 IMU ROS 2 node.

This launch file starts the icm20948_node with parameters loaded from the config/icm20948.yaml file.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generate the launch description for the ICM20948 IMU node.

    Returns:
        LaunchDescription: The launch description containing the node configuration.
    """
    pkg_share = get_package_share_directory("picarx")
    config = os.path.join(pkg_share, "config", "icm20948.yaml")

    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="icm20948_node",
                name="icm20948_node",
                output="screen",
                parameters=[config],
            ),
        ]
    )
