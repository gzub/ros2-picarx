"""
Launch file for the Picarx Speak Detections Node.

This launch file starts the speak detection node for the SunFounder PiCarX robot.
It is designed for use on Raspberry Pi OS (Pi 5) and is compatible with ROS 2 Jazzy.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generate the launch description for the Picarx Speak Detections Node.

    Returns:
        LaunchDescription: The launch description object for the ROS 2 launch system.
    """
    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="picarx_speak_detections",
                name="picarx_speak_detections_node",
                output="both",
                parameters=[],
            )
        ]
    )
