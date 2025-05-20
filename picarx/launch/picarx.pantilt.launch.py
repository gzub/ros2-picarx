"""
Launch file for the Picarx Pan-Tilt Node.

This launch file starts the pan-tilt node for the SunFounder PiCarX robot,
configuring the servo indices and angle limits for the Robot Hat v4 hardware.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    parameter_path = os.path.join(
        get_package_share_directory("picarx"), "config", "pantilt.yaml"
    )
    return LaunchDescription([
        Node(
            package="picarx",
            executable="picarx_pantilt",
            name="picarx_pantilt_node",
            output="both",
            parameters=[parameter_path],
        )
    ])
