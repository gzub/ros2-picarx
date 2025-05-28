"""
Launch file for the Raspberry Pi AI Camera Node for SunFounder PiCarX.

This launch file starts the object detection node from the raspberrypi_ai_camera_ros2
package with parameters suitable for the PiCarX robot and the IMX500-based AI camera.
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Generate the launch description for the Raspberry Pi AI Camera Node.

    Launches the object_detection_node with parameters loaded from YAML.
    """
    parameter_path = PathJoinSubstitution([
        FindPackageShare("picarx"),
        "config",
        "ai_camera.yaml"
    ])
    return LaunchDescription(
        [
            Node(
                package="raspberrypi_ai_camera_ros2",
                executable="object_detection_node",
                name="picarx_rpiai_camera_node",
                output="both",
                parameters=[parameter_path],
                remappings=[
                    # Add topic remappings here if needed, e.g., ('/old_topic', '/new_topic')
                ],
            )
        ]
    )
