"""
Launch file for the complete PiCarX ROS 2 system.

This launch file starts all core nodes and subsystems for the SunFounder PiCarX robot,
including Ackermann drive, ultrasonic sensor, grayscale sensor, AI camera, web video server,
joystick teleoperation, and object avoidance. It is designed for use on Raspberry Pi OS (Pi 5)
with Robot Hat v4 and ROS 2 Jazzy.
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Generate the launch description for the full PiCarX system.

    This function includes all required launch files for the robot's hardware interfaces,
    perception, teleoperation, and object avoidance subsystems.

    Returns:
        LaunchDescription: The launch description object for the ROS 2 launch system.
    """
    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.ackermann.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.ultrasonic.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.grayscale.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.ai_camera.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.web_video_server.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.joystick.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        FindPackageShare("object_avoidance"),
                        "/launch/object_avoidance.launch.py",
                    ]
                )
            ),
        ]
    )
