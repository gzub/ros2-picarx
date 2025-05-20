"""
Picarx Pan-Tilt Node for SunFounder PiCarX (Robot Hat v4, ROS 2 Jazzy).

This node controls two servos (pan and tilt) for a camera or sensor mount.
It subscribes to geometry_msgs/Vector3 messages on 'picarx/pantilt_cmd' and
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
"""

import threading

import rclpy
from geometry_msgs.msg import Vector3
from rclpy.node import Node

from robot_hat import Servo


class PicarxPantiltNode(Node):
    """
    ROS 2 node for controlling a pan-tilt mechanism using two servos.
    """

    def __init__(self):
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

        # Initialize servos
        self.pan_servo = Servo(self.pan_servo_index)
        self.tilt_servo = Servo(self.tilt_servo_index)

        # Store current angles
        self.current_pan = self.initial_pan
        self.current_tilt = self.initial_tilt

        # Lock for thread safety
        self._lock = threading.Lock()

        # Publisher for current angles
        self.angle_pub = self.create_publisher(Vector3, "picarx/pantilt_angles", 10)

        # Set initial angles from parameters
        self.set_angles(self.initial_pan, self.initial_tilt)

        # Subscribe to pan-tilt command topic
        self.subscription = self.create_subscription(
            Vector3, "picarx/pantilt_cmd", self.cmd_callback, 10
        )

        # Timer to periodically publish current angles
        self.timer = self.create_timer(0.5, self.publish_current_angles)

        self.get_logger().info("Picarx Pan-Tilt Node started.")

    def set_angles(self, pan: float, tilt: float):
        # Clamp angles
        with self._lock:
            pan = max(self.pan_min_angle, min(self.pan_max_angle, pan))
            tilt = max(self.tilt_min_angle, min(self.tilt_max_angle, tilt))
            self.get_logger().debug(f"Setting pan: {pan:.1f}°, tilt: {tilt:.1f}°")
            self.pan_servo.angle(pan)
            self.tilt_servo.angle(-tilt)
            self.current_pan = pan
            self.current_tilt = tilt
        self.publish_current_angles()

    def publish_current_angles(self):
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
        Callback for pan-tilt command topic.
        """
        self.get_logger().debug(
            f"Received pan/tilt command: pan={msg.x:.1f}°, tilt={msg.y:.1f}°"
        )
        # Reverse the y axis for tilt
        self.set_angles(msg.x, msg.y)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = PicarxPantiltNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info("Shutting down...")
    except Exception as e:
        print(f"exception: {e}")
        if node:
            node.get_logger().error(f"Unhandled exception: {e}")
    finally:
        if node:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
