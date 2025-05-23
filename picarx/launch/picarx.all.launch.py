"""
Launch file for the complete PiCarX ROS 2 system.

This launch file starts all core nodes and subsystems for the SunFounder PiCarX robot,
including Ackermann drive, ultrasonic sensor, grayscale sensor, AI camera, web video server,
joystick teleoperation, and object avoidance. It is designed for use on Raspberry Pi OS (Pi 5)
with Robot Hat v4 and ROS 2 Jazzy.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
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
                    Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_pan_static_tf',
            arguments=['0', '0', '0.05', '0', '0', '0', 'base_link', 'camera_pan_link']
        ),

        # Static transform publisher for camera_tilt_link
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_tilt_static_tf',
            arguments=['0', '0', '0.02', '0', '0', '0', 'camera_pan_link', 'camera_tilt_link']
        ),

        # Static transform publisher for camera_link
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_link_static_tf',
            arguments=['0', '0', '0.02', '0', '0', '0', 'camera_tilt_link', 'camera_link']
        ),

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
                    [FindPackageShare("picarx"), "/launch/picarx.sysinfo.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.detections.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.ai_camera.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        FindPackageShare("picarx"),
                        "/launch/picarx.web_video_server.launch.py",
                    ]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.joystick.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/picarx.pantilt.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        FindPackageShare("picarx"),
                        "/launch/object_avoidance.launch.py",
                    ]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/icm20948.launch.py"]
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [FindPackageShare("picarx"), "/launch/topic_controller.launch.py"]
                )
            ),
        ]
    )
