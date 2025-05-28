"""
Launch file for the Picarx Pan-Tilt Node.

This launch file starts the pan-tilt node for the SunFounder PiCarX robot,
configuring the servo indices and angle limits for the Robot Hat v4 hardware.
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    parameter_path = PathJoinSubstitution([
        FindPackageShare("picarx"),
        "config",
        "pantilt.yaml"
    ])
    return LaunchDescription([
        Node(
            package="picarx",
            executable="picarx_pantilt",
            name="picarx_pantilt_node",
            output="both",
            parameters=[parameter_path],
        )
    ])
