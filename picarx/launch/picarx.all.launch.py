"""
Launch file for the complete PiCarX ROS 2 system.

This launch file starts all core nodes and subsystems for the SunFounder PiCarX robot,
including Ackermann drive, ultrasonic sensor, grayscale sensor, AI camera, web video server,
joystick teleoperation, and object avoidance. It is designed for use on Raspberry Pi OS (Pi 5)
with Robot Hat v4 and ROS 2 Jazzy.
"""

from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def include_launch(pkg, launch_file):
    """
    Helper to create an IncludeLaunchDescription for a given package and launch file.

    Args:
        pkg (str): ROS2 package name.
        launch_file (str): Launch file name within the package's launch directory.

    Returns:
        IncludeLaunchDescription: Action to include the specified launch file.
    """
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare(pkg), f"/launch/{launch_file}"])
    )


def generate_launch_description():
    """
    Generate the launch description for the full PiCarX system.

    Groups and includes all required launch files for the robot's hardware interfaces,
    perception, teleoperation, and object avoidance subsystems.

    Returns:
        LaunchDescription: The composed launch description for the PiCarX system.
    """

    # Define launch files for each group
    hardware_launches = [
        "picarx.hardware.launch.py",
        "picarx.sysinfo.launch.py",
        "topic_controller.launch.py",
        "picarx.pantilt.launch.py",
        "picarx.joystick.launch.py",
    ]
    sensors_launches = [
        "icm20948.launch.py",
        "picarx.ultrasonic.launch.py",
        "picarx.grayscale.launch.py",
    ]
    perception_launches = [
        "ekf.launch.py",
        "picarx.detections.launch.py",
        "picarx.ai_camera.launch.py",
#        "picarx.web_video_server.launch.py",
        "object_avoidance.launch.py",
    ]

    hardware_group = GroupAction(
        [include_launch("picarx", lf) for lf in hardware_launches]
    )
    sensors_group = GroupAction(
        [include_launch("picarx", lf) for lf in sensors_launches]
    )
    perception_group = GroupAction(
        [include_launch("picarx", lf) for lf in perception_launches]
    )

    return LaunchDescription(
        [
            hardware_group,
            sensors_group,
            perception_group,
        ]
    )
