"""
Launch file for the Picarx Ultrasonic Node.

This launch file starts the ultrasonic sensor node for the SunFounder PiCarX robot,
configuring the node for use with the Robot Hat v4 hardware. It is designed for use
on Raspberry Pi OS (Pi 5) and is compatible with ROS 2 Jazzy.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generate the launch description for the Picarx Ultrasonic Node.

    Returns:
        LaunchDescription: The launch description object for the ROS 2 launch system.
    """
    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="picarx_ultrasonic",
                name="picarx_ultrasonic_node",
                output="both",
                parameters=[
                    # Add parameters here if needed, e.g., {'param_name': 'value'}
                ],
                remappings=[
                    # Add topic remappings here if needed, e.g., ('/old_topic', '/new_topic')
                ],
            )
        ]
    )
