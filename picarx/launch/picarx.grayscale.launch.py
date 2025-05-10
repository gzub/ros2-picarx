import os
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='picarx',  # Replace with your package name
            executable='picarx_grayscale',  # The entry point defined in setup.py
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