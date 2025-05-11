"""
Picarx Joystick Node.

This node subscribes to joystick inputs and publishes AckermannDrive
commands for the PiCarX robot. If the joystick is not moving, it continues
to publish a zeroed command at a fixed rate to ensure the robot stops.
"""

import rclpy
from rclpy.node import Node, QoSProfile
from rclpy.qos import HistoryPolicy, ReliabilityPolicy
from sensor_msgs.msg import Joy

from ackermann_msgs.msg import AckermannDrive


class PicarxJoystickNode(Node):
    """
    ROS 2 node that converts joystick input to AckermannDrive commands for the PiCarX robot.
    Publishes zero commands at a fixed rate when the joystick is at rest.
    """

    def __init__(self):
        """
        Initialize the PicarxJoystickNode.

        Sets up the publisher for AckermannDrive messages, subscribes to joystick input,
        and declares parameters for joystick mapping and scaling.
        """
        super().__init__("picarx_joystick_node")
        self.get_logger().info("Picarx Joystick Node has been started.")
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Publisher for AckermannDrive messages
        self.drive_publisher = self.create_publisher(
            AckermannDrive, "picarx/cmd_ackermann", qos_profile
        )

        # Subscriber to joystick messages
        self.joy_subscriber = self.create_subscription(
            Joy, "joy", self.joy_callback, qos_profile
        )

        # Parameters for joystick mapping
        self.declare_parameter("steering_axis", 0)
        self.declare_parameter("throttle_axis", 1)
        self.declare_parameter("max_steering_angle", 45.0)
        self.declare_parameter("max_speed", 100.0)
        self.declare_parameter("reverse_steering", False)
        self.declare_parameter("idle_publish_rate", 10.0)  # Hz

        self.last_joy_msg = None
        self.last_nonzero = False

        # Timer for publishing zero command when idle
        idle_period = 1.0 / self.get_parameter("idle_publish_rate").get_parameter_value().double_value
        self.idle_timer = self.create_timer(idle_period, self.idle_publish_callback)

    def joy_callback(self, msg: Joy):
        """
        Callback for joystick messages.

        Reads the joystick axes, applies scaling and direction parameters, and publishes
        an AckermannDrive command to control the robot.

        Args:
            msg (Joy): The incoming joystick message.
        """
        steering_axis = self.get_parameter("steering_axis").get_parameter_value().integer_value
        throttle_axis = self.get_parameter("throttle_axis").get_parameter_value().integer_value
        max_steering_angle = self.get_parameter("max_steering_angle").get_parameter_value().double_value
        max_speed = self.get_parameter("max_speed").get_parameter_value().double_value
        reverse_steering = self.get_parameter("reverse_steering").get_parameter_value().bool_value

        steering = msg.axes[steering_axis] * max_steering_angle
        if reverse_steering:
            steering = -steering
        speed = msg.axes[throttle_axis] * max_speed

        drive_msg = AckermannDrive()
        drive_msg.steering_angle = steering
        drive_msg.speed = speed
        self.drive_publisher.publish(drive_msg)

        # Save last message and whether it was nonzero
        self.last_joy_msg = msg
        self.last_nonzero = abs(steering) > 1e-3 or abs(speed) > 1e-3

    def idle_publish_callback(self):
        """
        Timer callback to publish a zero command if the joystick is idle.
        """
        # If last command was nonzero, do nothing (user is actively controlling)
        if self.last_nonzero:
            return

        # If no joystick message has ever been received, publish zero command
        if self.last_joy_msg is None:
            drive_msg = AckermannDrive()
            drive_msg.steering_angle = 0.0
            drive_msg.speed = 0.0
            self.drive_publisher.publish(drive_msg)
            return

        # If last joystick message was zero, republish zero command
        steering_axis = self.get_parameter("steering_axis").get_parameter_value().integer_value
        throttle_axis = self.get_parameter("throttle_axis").get_parameter_value().integer_value
        max_steering_angle = self.get_parameter("max_steering_angle").get_parameter_value().double_value
        max_speed = self.get_parameter("max_speed").get_parameter_value().double_value
        reverse_steering = self.get_parameter("reverse_steering").get_parameter_value().bool_value

        steering = self.last_joy_msg.axes[steering_axis] * max_steering_angle
        if reverse_steering:
            steering = -steering
        speed = self.last_joy_msg.axes[throttle_axis] * max_speed

        if abs(steering) < 1e-3 and abs(speed) < 1e-3:
            drive_msg = AckermannDrive()
            drive_msg.steering_angle = 0.0
            drive_msg.speed = 0.0
            self.drive_publisher.publish(drive_msg)

    def destroy_node(self):
        """
        Cleans up resources before shutting down the node.
        """
        self.get_logger().info("Shutting down Picarx Joystick Node.")
        super().destroy_node()


def main(args=None):
    """
    Main entry point for the PicarxJoystickNode.

    Initializes the ROS 2 node, spins it to process incoming messages, and
    ensures proper cleanup during shutdown.
    """
    rclpy.init(args=args)
    node = PicarxJoystickNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
