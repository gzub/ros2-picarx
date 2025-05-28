"""
Launch file for joystick teleoperation on the SunFounder PiCarX (Robot Hat v4, ROS 2 Jazzy).

This launch file starts the joy_linux driver and the Picarx joystick control node,
loading parameters from the joystick.yaml configuration file. It is designed for use
on Raspberry Pi OS (Pi 5) and is compatible with ROS 2 Jazzy and the SunFounder PiCarX hardware.
"""

import os
from pathlib import Path

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

SCRIPT_PATH = Path(os.path.realpath(__file__)).parent
CONFIG_PATH = SCRIPT_PATH.parent / "config"


def generate_launch_description():
    """
    Generate the launch description for joystick teleoperation.

    Loads parameters from the joystick.yaml configuration file and launches both the
    joy_linux driver and the Picarx joystick control node.

    Returns:
        LaunchDescription: The launch description object for the ROS 2 launch system.
    """
    parameter_path = PathJoinSubstitution(
        [FindPackageShare("picarx"), "config", "joystick.yaml"]
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
