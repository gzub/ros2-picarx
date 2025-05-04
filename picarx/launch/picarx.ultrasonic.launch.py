from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="picarx_ultrasonic",
                name="picarx_ultrasonic_node",
                output="screen",
                parameters=[
                    # Add parameters here if needed, e.g., {'param_name': 'value'}
                ],
                remappings=[
                    # Add topic remappings here if needed, e.g., ('/old_topic', '/new_topic')
                ],
            )
        ]
    )
