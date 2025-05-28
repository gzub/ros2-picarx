"""
Launch file for the Picarx Grayscale Node.

This launch file starts the grayscale sensor node for the SunFounder PiCarX robot,
configuring the ADC pins and reference values for the SunFounder Robot Hat v4 hardware.
It is designed for use on Raspberry Pi OS (Pi 5) and is compatible with ROS 2 Jazzy.
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Generate the launch description for the Picarx Grayscale Node.

    Returns:
        LaunchDescription: The launch description object for the ROS 2 launch system.
    """
    parameter_path = PathJoinSubstitution([
        FindPackageShare("picarx"),
        "config",
        "grayscale_sensor.yaml"
    ])
    return LaunchDescription([
        Node(
            package='picarx',
            executable='picarx_grayscale',
            name='picarx_grayscale_node',
            output='both',
            parameters=[parameter_path]
        )
    ])
