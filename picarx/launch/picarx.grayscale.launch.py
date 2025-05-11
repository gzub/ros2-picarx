"""
Launch file for the Picarx Grayscale Node.

This launch file starts the grayscale sensor node for the SunFounder PiCarX robot,
configuring the ADC pins and reference values for the SunFounder Robot Hat v4 hardware.
It is designed for use on Raspberry Pi OS (Pi 5) and is compatible with ROS 2 Jazzy.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generate the launch description for the Picarx Grayscale Node.

    Returns:
        LaunchDescription: The launch description object for the ROS 2 launch system.
    """
    return LaunchDescription([
        Node(
            package='picarx',
            executable='picarx_grayscale',
            name='picarx_grayscale_node',
            output='both',
            parameters=[
                {
                    'adc_pins': [0, 1, 2],  # Default ADC pins
                    'reference_values': [500, 500, 500]  # Default reference values
                }
            ]
        )
    ])
