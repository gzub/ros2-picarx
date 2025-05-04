from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="picarx",
                executable="picarx_ackermann",
                name="picarx_ackermann_node",
                output="screen",
                parameters=[
                    {"max_speed": 100.0},  # Maximum speed
                    {"max_steering_angle": 45.0},  # Maximum steering angle in degrees
                    {
                        "steering_angle_offset": -4.5
                    },  # Calibration offset for steering angle
                ],
                remappings=[
                    # Add topic remappings here if needed, e.g., ('/old_topic', '/new_topic')
                ],
            )
        ]
    )
