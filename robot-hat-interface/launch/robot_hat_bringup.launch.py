import launch
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import LifecycleNode
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node

import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    robot_description_content = Command(
        ['xacro', ' ', LaunchConfiguration('model')]
    )

    robot_description = {
        'robot_description': ParameterValue(robot_description_content, value_type=str)
    }

    controller_yaml = os.path.join(
        get_package_share_directory('robot_hat_interface'),
        'config',
        'my_controllers.yaml'
    )

    # Nodes
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace='robot_hat_interface',
        output='both',
        parameters=[robot_description]  # Ensure this contains the correct robot description
    )

    controller_manager_node = LifecycleNode(
        package='controller_manager',
        executable='ros2_control_node',
        name='controller_manager',
        namespace='robot_hat_interface',
        output='both',
        parameters=[
            robot_description,
            controller_yaml
        ],
    )
    
    # Load controller configurations
    load_joint_state_broadcaster = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'joint_state_broadcaster'],
        output='screen'
    )
    load_forward_command_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'forward_command_controller'],
        output='screen'
    )

    controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        namespace='robot_hat_interface',  # Ensure this matches the namespace
        arguments=['joint_state_broadcaster', '--controller-manager', '/robot_hat_interface/controller_manager']
    )

    return launch.LaunchDescription([
        DeclareLaunchArgument(
            name='model',
            default_value=os.path.join(get_package_share_directory('robot_hat_interface'),
                                        'urdf', 'picarx.urdf.xacro'),
            description='Full path to robot description xacro file'
        ),
        robot_state_publisher_node,
        controller_manager_node,
        load_joint_state_broadcaster,
        load_forward_command_controller,
        controller_spawner
    ])
