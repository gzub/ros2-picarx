import os
from pathlib import Path

import xacro
from launch import LaunchDescription
from launch_ros.actions import Node

SCRIPT_PATH = Path(os.path.realpath(__file__)).parent
CONFIG_PATH = SCRIPT_PATH.parent / "config"



def generate_launch_description():
    """
    Launch PiCarX ROS 2 control stack:
      - Processes the Xacro robot description for the PiCarX.
      - Launches robot_state_publisher to publish TF and robot state.
      - Launches ros2_control_node with robot description and controller config.
      - Spawns joint_state_broadcaster and ackermann_steering_controller.
    """
    # Paths
    urdf_path = SCRIPT_PATH.parent / "script" / "picarx.urdf.xacro"
    ros2_controllers_file = CONFIG_PATH / "ros2_controllers.yaml"

    # Check if URDF file exists
    if not urdf_path.exists():
        raise FileNotFoundError(f"URDF file not found: {urdf_path}")

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
                remappings=[
                    # ("ackermann_steering_controller/odometry", "odom"),
                    ("ackermann_steering_controller/tf_odometry", "tf"),
                    ("ackermann_steering_controller/tf_static", "tf_static"),
                ],
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
