#!/usr/bin/env python3
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generates a launch description for the Extended Kalman Filter (EKF) node.

    This launch file initializes the 'ekf_node' from the 'robot_localization' package,
    which performs sensor fusion using an Extended Kalman Filter to estimate the robot's pose.
    It loads the configuration from 'ekf.yaml' and remaps the filtered odometry topic
    to '/odom'.
    """
    config_dir = os.path.join(get_package_share_directory("picarx"), "config")
    ekf_config = os.path.join(config_dir, "ekf.yaml")

    ekf_node = Node(
        # The 'robot_localization' package provides state estimation nodes for robots.
        # The 'ekf_node' executable implements an Extended Kalman Filter (EKF) for sensor fusion,
        # combining data from multiple sensors (e.g., IMU, odometry) to estimate the robot's pose.
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        output="screen",
        parameters=[ekf_config],
        remappings=[("/odometry/filtered", "/odom")],  # Remap filtered odometry topic
    )

    return LaunchDescription([ekf_node])
