import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    parameter_path = os.path.join(
        get_package_share_directory("picarx"), "config", "picarx_ackermann_node.yaml"
    )

    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="picarx_ackermann",
                name="picarx_ackermann_node",
                output="both",
                parameters=[parameter_path],
                remappings=[
                    # Add topic remappings here if needed, e.g., ('/old_topic', '/new_topic')
                ],
            )
        ]
    )
