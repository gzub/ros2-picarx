"""
Launch file for the Picarx Ackermann Node.

This launch file starts the picarx_ackermann node with parameters loaded from
the configuration YAML file. It is designed for use with the SunFounder PiCarX
on Raspberry Pi OS (Pi 5) and Robot Hat v4.
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Generate the launch description for the Picarx Ackermann Node.

    Loads parameters from the YAML configuration file and launches the node.
    Returns:
        LaunchDescription: The launch description object for ROS 2 launch system.
    """
    parameter_path = PathJoinSubstitution(
        [FindPackageShare("picarx"), "config", "hardware.yaml"]
    )

    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="picarx_hardware",
                name="picarx_hardware_node",
                output="both",
                parameters=[parameter_path],
                remappings=[
                    # Add topic remappings here if needed, e.g., ('/old_topic', '/new_topic')
                ],
            )
        ]
    )
