"""
Picarx Joystick Node.

This node subscribes to joystick inputs and publishes Twist
commands for the PiCarX robot. If the joystick is not moving, it continues
to publish a zeroed command at a fixed rate to ensure the robot stops.
"""

import math

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node, QoSProfile
from rclpy.qos import HistoryPolicy, ReliabilityPolicy
from sensor_msgs.msg import Joy


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

        Parameters:
            - wheelbase: The distance between the front and rear axles of the robot (in meters).
              This parameter is used in the Ackermann steering geometry to calculate the angular
              velocity (yaw rate) of the robot based on the steering angle and speed.
        """
        super().__init__("picarx_joystick_node")
        self.get_logger().info("Picarx Joystick Node has been started.")
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Publisher for TwistStamped messages (Ackermann controller reference)
        self.drive_publisher = self.create_publisher(
            TwistStamped, "/ackermann_steering_controller/reference", qos_profile
        )

        # Subscriber to joystick messages
        self.joy_subscriber = self.create_subscription(
            Joy, "joy", self.joy_callback, qos_profile
        )

        # Parameters for joystick mapping and frame configuration
        self.declare_parameter("frame_id", "base_link")  # Default frame_id for robot base
        self.declare_parameter("steering_axis", 0)
        self.declare_parameter("throttle_axis", 1)
        self.declare_parameter("max_steering_angle", 45.0)
        self.declare_parameter("max_speed", 1.0)
        self.declare_parameter("reverse_steering", False)
        self.declare_parameter("idle_publish_rate", 10.0)  # Hz
        self.declare_parameter("wheelbase", 0.165)  # meters, adjust as needed
        idle_publish_rate = self.get_parameter("idle_publish_rate").get_parameter_value().double_value
        if idle_publish_rate <= 0.0:
            self.get_logger().warn(
                "Parameter 'idle_publish_rate' must be greater than 0.0. Using default value of 10.0 Hz."
            )
            idle_publish_rate = 10.0  # Default value

        idle_period = 1.0 / idle_publish_rate
        # Timer for publishing zero command when idle
        idle_period = (
            1.0
            / self.get_parameter("idle_publish_rate").get_parameter_value().double_value
        )
        self.idle_timer = self.create_timer(idle_period, self.idle_publish_callback)
        self.last_joy_msg = None  # Store the last joystick message
        self.last_nonzero = False  # Track if the last command was nonzero

        
    def joy_callback(self, msg: Joy):
        """
        Callback for joystick messages.

        Reads the joystick axes, applies scaling and direction parameters, and publishes
        a TwistStamped command to control the robot.

        Args:
            msg (Joy): The incoming joystick message.
        """
        # Get parameters
        steering_axis = (
            self.get_parameter("steering_axis").get_parameter_value().integer_value
        )
        throttle_axis = (
            self.get_parameter("throttle_axis").get_parameter_value().integer_value
        )
        max_steering_angle = (
            self.get_parameter("max_steering_angle").get_parameter_value().double_value
        )
        max_speed = self.get_parameter("max_speed").get_parameter_value().double_value
        reverse_steering = (
            self.get_parameter("reverse_steering").get_parameter_value().bool_value
        )
        wheelbase = self.get_parameter("wheelbase").get_parameter_value().double_value

        # Always read both axes and set both fields, even if only one is nonzero
        steering = msg.axes[steering_axis] * max_steering_angle
        if reverse_steering:
            steering = -steering
        # Only log steering axis value at debug level
        self.get_logger().debug(
            f"Steering axis value: {msg.axes[steering_axis]} (after scaling: {steering})"
        )
        speed = msg.axes[throttle_axis] * max_speed

        # Convert steering from degrees to radians
        steering_rad = math.radians(steering)

        # Set speed to zero if near zero
        if abs(speed) < 1e-6:
            speed = 0.0

        # Calculate angular.z using Ackermann steering geometry
        if abs(steering_rad) > 1e-6:
            angular_z = speed / wheelbase * math.tan(steering_rad)
            # Only log calculated angular.z at debug level
            self.get_logger().debug(
                f"Calculated angular.z: {angular_z:.3f} (steering_rad={steering_rad:.8f}, speed={speed:.8f})"
            )
        else:
            angular_z = 0.0

        twist_msg = TwistStamped()
        twist_msg.header.stamp = self.get_clock().now().to_msg()
        twist_msg.header.frame_id = self.get_parameter("frame_id").get_parameter_value().string_value  # Set frame_id from parameter
        twist_msg.twist.linear.x = speed
        twist_msg.twist.angular.z = angular_z  # calculated yaw rate

        self.drive_publisher.publish(twist_msg)

        # Save last message and whether it was nonzero
        self.last_joy_msg = msg
        self.last_nonzero = abs(steering_rad) > 1e-6 or abs(speed) > 1e-6

    def idle_publish_callback(self):
        """
        Timer callback to publish a zero command if the joystick is idle.
        """
        # If no joystick message has ever been received, do not publish
        if self.last_joy_msg is None:
            return

        # If last command was nonzero, publish zero command and reset flag
        if not self.last_nonzero:
            twist_msg = TwistStamped()
            twist_msg.header.stamp = self.get_clock().now().to_msg()
            twist_msg.twist.linear.x = 0.0
            twist_msg.twist.angular.z = 0.0
            self.drive_publisher.publish(twist_msg)
        # Always reset last_nonzero to False after idle publish
        self.last_nonzero = False

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
    node = None
    try:
        node = PicarxJoystickNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info("Shutting down...")
    except Exception as e:
        if node:
            node.get_logger().error(f"Unhandled exception: {e}")
    finally:
        if node:
            node.destroy_node()
        rclpy.shutdown()
