"""
Picarx Joystick Node.

This node subscribes to joystick inputs and publishes AckermannDrive
commands for the PiCarX robot.
"""

import os
from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from ackermann_msgs.msg import AckermannDrive

class PicarxJoystickNode(Node):
    def __init__(self):
        super().__init__("picarx_joystick_node")
        self.get_logger().info("Picarx Joystick Node has been started.")

        # Publisher for AckermannDrive messages
        self.drive_publisher = self.create_publisher(AckermannDrive, "picarx/cmd_ackermann", 10)

        # Subscriber to joystick messages
        self.joy_subscriber = self.create_subscription(Joy, "joy", self.joy_callback, 10)

        # Parameters for joystick mapping
        self.declare_parameter("steering_axis", 0)  # Default: Left stick horizontal axis
        self.declare_parameter("throttle_axis", 1)  # Default: Left stick vertical axis
        self.declare_parameter("max_steering_angle", 45.0)  # Max steering angle in degrees
        self.declare_parameter("max_speed", 100.0)  # Max speed in m/s
        self.declare_parameter("reverse_steering", False)  # Reverse steering direction

    def joy_callback(self, msg: Joy):
        # Get parameters
        self.get_logger().debug(f"Received joystick message: {msg}.")
        steering_axis = self.get_parameter("steering_axis").get_parameter_value().integer_value
        throttle_axis = self.get_parameter("throttle_axis").get_parameter_value().integer_value
        max_steering_angle = self.get_parameter("max_steering_angle").get_parameter_value().double_value
        max_speed = self.get_parameter("max_speed").get_parameter_value().double_value
        reverse_steering = self.get_parameter("reverse_steering").get_parameter_value().bool_value
        # Map joystick inputs to AckermannDrive message
        steering = msg.axes[steering_axis] * max_steering_angle
        if reverse_steering:
            steering = -steering  # Reverse the steering direction if the parameter is True
        speed = msg.axes[throttle_axis] * max_speed

        # Publish the drive command
        drive_msg = AckermannDrive()
        drive_msg.steering_angle = steering
        drive_msg.speed = speed
        self.drive_publisher.publish(drive_msg)

        self.get_logger().debug(f"Published drive command: steering={steering:.2f}, speed={speed:.2f}")

def main(args=None):
    rclpy.init(args=args)
    node = PicarxJoystickNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()