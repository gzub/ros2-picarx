"""
Launch file for the Picarx Speak Detections Node.

This launch file starts the speak detection node for the SunFounder PiCarX robot.
It is designed for use on Raspberry Pi OS (Pi 5) and is compatible with ROS 2 Jazzy.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generate the launch description for the Picarx Speak Detections Node.

    Returns:
        LaunchDescription: The launch description object for the ROS 2 launch system.
    """
    config_path = os.path.join(
        get_package_share_directory("picarx"), "config", "detections.yaml"
    )
    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="picarx_detections",
                name="picarx_detections_node",
                output="both",
                parameters=[config_path],
            )
        ]
    )
