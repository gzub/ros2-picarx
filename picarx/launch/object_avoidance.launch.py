from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    parameter_path = PathJoinSubstitution([
        FindPackageShare("picarx"),
        "config",
        "object_avoidance.yaml"
    ])
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
