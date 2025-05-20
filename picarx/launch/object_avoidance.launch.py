import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    parameter_path = os.path.join(
        get_package_share_directory("picarx"), "config", "object_avoidance.yaml"
    )
    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="object_avoidance",
                name="object_avoidance_node",
                output="both",
                parameters=[parameter_path],
            )
        ]
    )
