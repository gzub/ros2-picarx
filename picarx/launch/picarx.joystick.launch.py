import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    parameter_path = os.path.join(
        get_package_share_directory("picarx"), "config", "joystick.yaml"
    )

    return LaunchDescription(
        [
            # Start the joy_linux driver
            Node(
                package="joy_linux",
                executable="joy_linux_node",
                name="joy_linux_node",
                parameters=[parameter_path],
            ),
            # Start the Picarx joystick control node
            Node(
                package="picarx",
                executable="picarx_joystick",
                name="picarx_joystick_node",
                parameters=[parameter_path],
            ),
        ]
    )
