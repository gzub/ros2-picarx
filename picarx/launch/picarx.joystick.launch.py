from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Start the joy_linux driver
        Node(
            package="joy_linux",
            executable="joy_linux_node",
            name="joy_linux_node",
            parameters=[{
                "dev_name": "/dev/input/event6",  # Adjust this to your joystick device
                "deadzone": 0.1,
                # "autorepeat_rate": 0.0,
                # "coalesce_interval": 0.05,
                "reverse_steering": True,
            }],
        ),
        # Start the Picarx joystick control node
        Node(
            package="picarx",
            executable="picarx_joystick",
            name="picarx_joystick_node",
            parameters=[{
                "steering_axis": 3,
                "throttle_axis": 1,
                "max_steering_angle": 35.0,
                "max_speed": 100.0,
            }],
        ),
    ])