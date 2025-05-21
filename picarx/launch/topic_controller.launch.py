import os
from pathlib import Path

import xacro
from launch import LaunchDescription
from launch_ros.actions import Node

SCRIPT_PATH = Path(os.path.realpath(__file__)).parent
CONFIG_PATH = SCRIPT_PATH.parent / "config"


def generate_launch_description():
    """
    Generate a LaunchDescription for the PiCarX ROS 2 control stack.

    This launch file:
      - Processes the Xacro robot description for the PiCarX.
      - Launches the robot_state_publisher node to publish TF and robot state.
      - Launches the ros2_control_node with the robot description and controller configuration.
      - Spawns the joint_state_broadcaster and ackermann_steering_controller.

    Returns:
        LaunchDescription: The launch description containing all required nodes.
    """
    # Paths
    urdf_path = SCRIPT_PATH.parent / "script" / "picarx.urdf.xacro"
    ros2_controllers_file = CONFIG_PATH / "ros2_controllers.yaml"

    # Process xacro to robot_description
    robot_description = {
        "robot_description": xacro.process_file(str(urdf_path)).toxml(),
    }

    # List of controllers to spawn
    controllers = [
        "joint_state_broadcaster",
        "ackermann_steering_controller",
    ]

    # LaunchDescription with all nodes
    return LaunchDescription(
        [
            # Publishes TF and robot state
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                parameters=[robot_description],
                output="screen",
            ),
            # Starts ros2_control with robot description and controllers config
            Node(
                package="controller_manager",
                executable="ros2_control_node",
                parameters=[robot_description, str(ros2_controllers_file)],
                output="screen",
            ),
        ]
        + [
            # Spawns each controller
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[controller],
                output="screen",
            )
            for controller in controllers
        ]
    )
