"""
Picarx Pan-Tilt Node for SunFounder PiCarX (Robot Hat v4, ROS 2 Kilted).

This node controls two servos (pan and tilt) for a camera or sensor mount.
It subscribes to geometry_msgs/Vector3 messages on '/pantilt_cmd' and
sets the servo angles accordingly.

Parameters:
- pan_servo_index: int (default: 0)
- tilt_servo_index: int (default: 1)
- pan_min_angle: float (default: -90)
- pan_max_angle: float (default: 90)
- tilt_min_angle: float (default: -90)
- tilt_max_angle: float (default: 90)
- initial_pan: float (default: 0)
- initial_tilt: float (default: 0)
- frame_id: str (default: 'camera_pan_link')
"""

import threading
import math

import rclpy
from geometry_msgs.msg import Vector3
from rclpy.node import Node
from sensor_msgs.msg import JointState

from picarx.robot_hat_interface import DirectI2CServo


class PicarxPantiltNode(Node):
    """
    ROS 2 node for controlling a pan-tilt mechanism using two servos.

    Publishes:
        /pantilt_angles (geometry_msgs/Vector3): Current pan/tilt angles in degrees.
        /joint_states (sensor_msgs/JointState): Joint states for robot_state_publisher.

    Subscribes:
        /pantilt_cmd (geometry_msgs/Vector3): Desired pan/tilt angles in degrees.

    Parameters:
        pan_servo_index (int): Servo index for pan axis.
        tilt_servo_index (int): Servo index for tilt axis.
        pan_min_angle (float): Minimum pan angle (deg).
        pan_max_angle (float): Maximum pan angle (deg).
        tilt_min_angle (float): Minimum tilt angle (deg).
        tilt_max_angle (float): Maximum tilt angle (deg).
        initial_pan (float): Initial pan angle (deg).
        initial_tilt (float): Initial tilt angle (deg).
        frame_id (str): Frame ID for published messages.
    """

    def __init__(self):
        """
        Initialize the PicarxPantiltNode, declare parameters, set up publishers,
        subscribers, timers, and initialize servos.
        """
        super().__init__("picarx_pantilt_node")

        # Declare parameters
        self.declare_parameter("pan_servo_index", 0)
        self.declare_parameter("tilt_servo_index", 1)
        self.declare_parameter("pan_min_angle", -90.0)
        self.declare_parameter("pan_max_angle", 90.0)
        self.declare_parameter("tilt_min_angle", -90.0)
        self.declare_parameter("tilt_max_angle", 90.0)
        self.declare_parameter("initial_pan", 0.0)
        self.declare_parameter("initial_tilt", 0.0)
        self.declare_parameter("frame_id", "camera_link")

        # Get parameters
        self.pan_servo_index = (
            self.get_parameter("pan_servo_index").get_parameter_value().integer_value
        )
        self.tilt_servo_index = (
            self.get_parameter("tilt_servo_index").get_parameter_value().integer_value
        )
        self.pan_min_angle = (
            self.get_parameter("pan_min_angle").get_parameter_value().double_value
        )
        self.pan_max_angle = (
            self.get_parameter("pan_max_angle").get_parameter_value().double_value
        )
        self.tilt_min_angle = (
            self.get_parameter("tilt_min_angle").get_parameter_value().double_value
        )
        self.tilt_max_angle = (
            self.get_parameter("tilt_max_angle").get_parameter_value().double_value
        )
        self.initial_pan = (
            self.get_parameter("initial_pan").get_parameter_value().double_value
        )
        self.initial_tilt = (
            self.get_parameter("initial_tilt").get_parameter_value().double_value
        )
        self.frame_id = (
            self.get_parameter("frame_id").get_parameter_value().string_value
        )

        # Initialize servos using DirectI2CServo from robot_hat_interface
        self.pan_servo = DirectI2CServo(self.pan_servo_index)
        self.tilt_servo = DirectI2CServo(self.tilt_servo_index)

        # Store current angles
        self.current_pan = self.initial_pan
        self.current_tilt = self.initial_tilt

        # Lock for thread safety
        self._lock = threading.Lock()

        # Publisher for current angles (with header for time/frame_id)
        self.angle_pub = self.create_publisher(Vector3, "/pantilt_angles", 10)

        # Publisher for joint states (for robot_state_publisher)
        self.joint_state_pub = self.create_publisher(JointState, "/joint_states", 10)

        # Set initial angles from parameters
        self.set_angles(self.initial_pan, self.initial_tilt)

        # Subscribe to pan-tilt command topic
        self.subscription = self.create_subscription(
            Vector3, "/pantilt_cmd", self.cmd_callback, 10
        )

        # Timer to periodically publish current angles
        self.timer = self.create_timer(0.5, self.publish_current_angles)
        # Add a timer to periodically publish joint states for TF
        self.joint_state_timer = self.create_timer(
            0.05, lambda: self.publish_joint_states(self.current_pan, self.current_tilt)
        )

        self.get_logger().info("Picarx Pan-Tilt Node started.")

    def set_angles(self, pan: float, tilt: float):
        """
        Set the pan and tilt angles, clamp to limits, actuate servos,
        and publish updated joint states and angles.

        Args:
            pan (float): Desired pan angle in degrees.
            tilt (float): Desired tilt angle in degrees.
        """
        # Clamp angles
        with self._lock:
            pan = max(self.pan_min_angle, min(self.pan_max_angle, pan))
            tilt = max(self.tilt_min_angle, min(self.tilt_max_angle, tilt))
            self.get_logger().debug(f"Setting pan: {pan:.1f}°, tilt: {tilt:.1f}°")
            self.pan_servo.angle(pan)
            # For most pan/tilt heads, positive tilt is up; reverse if needed
            self.tilt_servo.angle(-tilt)
            self.current_pan = pan
            self.current_tilt = tilt
        # Publish joint states and current angles while holding the lock
        self.publish_current_angles()
        self.publish_joint_states(pan, tilt)

    def publish_joint_states(self, pan_deg, tilt_deg):
        """
        Publish the current pan and tilt angles as a JointState message
        for robot_state_publisher.

        Args:
            pan_deg (float): Pan angle in degrees.
            tilt_deg (float): Tilt angle in degrees.
        """
        # Publish pan/tilt as joint states in radians
        js = JointState()
        js.header.frame_id = "base_link"  # Use base_link for robot state
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = ["camera_pan_joint", "camera_tilt_joint"]
        js.position = [math.radians(pan_deg), math.radians(tilt_deg)]
        self.joint_state_pub.publish(js)

    def publish_current_angles(self):
        """
        Publish the current pan and tilt angles as a Vector3 message.
        """
        with self._lock:
            pan = self.current_pan
            tilt = self.current_tilt
        msg = Vector3()
        msg.x = pan
        msg.y = tilt
        msg.z = 0.0
        self.get_logger().debug(
            f"Publishing current angles: pan={msg.x:.1f}°, tilt={msg.y:.1f}°"
        )
        self.angle_pub.publish(msg)

    def cmd_callback(self, msg: Vector3):
        """
        Callback for pan-tilt command topic. Sets new pan/tilt angles.

        Args:
            msg (geometry_msgs.msg.Vector3): Commanded pan (x) and tilt (y) angles in degrees.
        """
        self.get_logger().debug(
            f"Received pan/tilt command: pan={msg.x:.1f}°, tilt={msg.y:.1f}°"
        )
        self.set_angles(msg.x, msg.y)


def main(args=None):
    """
    Main entry point for the node. Initializes ROS, spins the node,
    and handles shutdown.
    """
    rclpy.init(args=args)
    node = None
    try:
        node = PicarxPantiltNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info("Shutting down...")
    except Exception as e:
        if node:
            node.get_logger().error(f"Unhandled exception: {e}")
        else:
            print(f"Unhandled exception: {e}")
    finally:
        if node:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
