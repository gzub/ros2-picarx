"""
Launch file for the web_video_server node for SunFounder PiCarX.

This launch file starts the web_video_server node, which provides a web interface
for streaming ROS 2 image topics. It is designed for use on Raspberry Pi OS (Pi 5)
and is compatible with ROS 2 Jazzy and the SunFounder PiCarX hardware.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generate the launch description for the web_video_server node.

    Returns:
        LaunchDescription: The launch description object for the ROS 2 launch system.
    """
    return LaunchDescription(
        [
            Node(
                package="web_video_server",
                executable="web_video_server",
                name="picarx_web_video_server_node",
                output="both",
                parameters=[],
                remappings=[
                    # Add topic remappings here if needed, e.g., ('/old_topic', '/new_topic')
                ],
            )
        ]
    )
