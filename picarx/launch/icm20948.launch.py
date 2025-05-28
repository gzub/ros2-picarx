"""
Launch file for the ICM20948 IMU ROS 2 node.

This launch file starts the icm20948_node with parameters loaded from the config/icm20948.yaml file.
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Generate the launch description for the ICM20948 IMU node.

    Returns:
        LaunchDescription: The launch description containing the node configuration.
    """
    config = PathJoinSubstitution(
        [FindPackageShare("picarx"), "config", "icm20948.yaml"]
    )

    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="icm20948_node",
                name="icm20948_node",
                output="screen",
                parameters=[config],
            )
        ]
    )
