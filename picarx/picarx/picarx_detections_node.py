"""
Picarx Speak Detections Node

This ROS 2 node subscribes to the /camera/detections topic (vision_msgs/Detection2DArray),
extracts detected object labels, and uses the Raspberry Pi speaker to announce what was detected.
It uses espeak for speech synthesis and the robot_hat package to enable/disable the speaker.

Additionally, it centers the pan/tilt camera on the most recently detected object by publishing
commands to the pan/tilt controller node.

Compatible with Raspberry Pi OS, PiCarX, and Robot Hat v4.
"""

import os
import subprocess
import threading

import rclpy
from geometry_msgs.msg import Vector3
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray

from picarx.robot_hat_interface import Pin, PinMode


class PicarxSpeakDetectionsNode(Node):
    """
    Node that speaks detected objects using the onboard speaker,
    and centers the camera on the most recently detected object.

    Subscribes:
        /camera/detections (vision_msgs/Detection2DArray): Object detection results.
        /pantilt_angles (geometry_msgs/Vector3): Current pan/tilt angles.

    Publishes:
        /pantilt_cmd (geometry_msgs/Vector3): Desired pan/tilt angles.
    """

    def __init__(self):
        """
        Initialize the PicarxSpeakDetectionsNode.
        Sets up subscriptions, publishers, and initial state.
        """
        super().__init__("picarx_detections_node")
        # Declare parameters for speaking, image size, and dead zone
        self.declare_parameter("enable_speaking", True)
        self.declare_parameter("image_width", 640)
        self.declare_parameter("image_height", 480)
        self.declare_parameter("dead_zone", 0.15)
        try:
            self.enable_speaking = (
                self.get_parameter("enable_speaking").get_parameter_value().bool_value
            )
        except AttributeError:
            self.get_logger().warn(
                "Invalid value for 'enable_speaking'. Using default: True."
            )
            self.enable_speaking = True

        # Declare parameters for proportional control gains
        self.declare_parameter("k_pan", 2.5)
        self.declare_parameter("k_tilt", 1.0)
        self.k_pan = self.get_parameter("k_pan").get_parameter_value().double_value
        self.k_tilt = self.get_parameter("k_tilt").get_parameter_value().double_value
        self.image_width = (
            self.get_parameter("image_width").get_parameter_value().integer_value
        )
        self.image_height = (
            self.get_parameter("image_height").get_parameter_value().integer_value
        )
        self.dead_zone = (
            self.get_parameter("dead_zone").get_parameter_value().double_value
        )
        self.subscription = self.create_subscription(
            Detection2DArray, "/camera/detections", self.detection_callback, 10
        )
        self.tilt_pan_pub = self.create_publisher(Vector3, "/pantilt_cmd", 10)
        self.pantilt_angle_sub = self.create_subscription(
            Vector3, "/pantilt_angles", self.pantilt_angle_callback, 10
        )
        self.last_spoken = set()
        self.pan = 0.0  # Current pan angle/state
        self.tilt = 0.0  # Current tilt angle/state
        self.d_pan = 0.0  # Desired pan angle
        self.d_tilt = 0.0  # Desired tilt angle
        self._lock = threading.Lock()
        self._speaker_device = None  # Pin instance for speaker GPIO
        self.get_logger().info("PicarxSpeakDetectionsNode started.")

    def pantilt_angle_callback(self, msg: Vector3):
        """
        Callback for receiving current pan/tilt angles from the pantilt node.

        Args:
            msg (geometry_msgs.msg.Vector3): Current pan (x) and tilt (y) angles.
        """
        self.get_logger().debug(
            f"Received pan/tilt angles: pan={msg.x:.2f}, tilt={msg.y:.2f}"
        )
        with self._lock:
            self.pan = msg.x
            self.tilt = msg.y

    def detection_callback(self, msg: Detection2DArray):
        """
        Callback for processing detection results.

        - Extracts detected object labels.
        - Announces new detections via speaker.
        - Computes and publishes pan/tilt commands to center the most recent detection.

        Args:
            msg (vision_msgs.msg.Detection2DArray): Detection results.
        """
        self.get_logger().debug(f"Received {len(msg.detections)} detections.")
        detected_labels = set()
        # Center camera on the most recently detected object (last in list)
        if msg.detections:
            self.get_logger().debug(
                "Processing most recent detection for pan/tilt centering."
            )
            bbox = msg.detections[-1].bbox
            label = msg.detections[-1].results[0].hypothesis.class_id
            cx = bbox.center.position.x
            cy = bbox.center.position.y
            # Calculate error from image center
            err_x = (cx - self.image_width / 2) / (self.image_width / 2)
            err_y = (cy - self.image_height / 2) / (self.image_height / 2)
            # Dead zone: do not move if error is small
            dead_zone = self.dead_zone
            if abs(err_x) < dead_zone and abs(err_y) < dead_zone:
                self.get_logger().debug(
                    f"Detection '{label}' is within dead zone. No pan/tilt command sent."
                )
                self.get_logger().debug(
                    f"Detected: {label}, bbox center=({cx:.1f},{cy:.1f}), "
                    f"err_x={err_x:.2f}, err_y={err_y:.2f} -- within dead zone, no pan/tilt command."
                )
            else:
                # Simple proportional control using configurable gains
                with self._lock:
                    self.d_pan = self.pan + (-err_x * self.k_pan)
                    self.d_tilt = self.tilt + (-err_y * self.k_tilt)

                self.get_logger().debug(
                    f"Detected: {label}, "
                    f"Tilt/Pan movement: bbox center=({cx:.1f},{cy:.1f}), "
                    f"err_x={err_x:.2f}, err_y={err_y:.2f}, "
                    f"pan: {self.d_pan:.1f}, tilt: {self.d_tilt:.1f}"
                )
                cmd = Vector3()
                cmd.x = self.d_pan
                cmd.y = self.d_tilt
                cmd.z = 0.0
                self.tilt_pan_pub.publish(cmd)
                self.get_logger().debug(
                    f"Published pan/tilt command: pan={cmd.x:.2f}, tilt={cmd.y:.2f}"
                )
        for detection in msg.detections:
            if detection.results:
                label = detection.results[0].hypothesis.class_id
                detected_labels.add(label)
        if not detected_labels:
            self.get_logger().debug("No valid detection labels found.")
            return

        # Only speak new detections
        with self._lock:
            new_labels = detected_labels - self.last_spoken
            if not new_labels:
                self.get_logger().debug("No new detections to speak.")
                return
            phrase = "I see a " + ", ".join(new_labels)
            self.get_logger().debug(f"New detections to speak: {phrase}")
            self.last_spoken = detected_labels

        self.get_logger().info(f"Speaking: {phrase}")

        if self.enable_speaking:
            self.get_logger().debug("Enabling speaker and speaking phrase.")
            try:
                self._enable_speaker()
                subprocess.run(["espeak", phrase], check=True)
            except Exception as e:
                self.get_logger().error(f"Failed to speak: {e}")
            finally:
                self._disable_speaker()
                self.get_logger().debug("Speaker disabled after speaking.")
        else:
            self.get_logger().debug("Speaking is disabled by parameter.")

    def _get_speaker_device(self):
        """
        Returns a Pin instance for the speaker pin (auto-detected, output mode).
        Only creates the Pin once and reuses it, avoiding double allocation errors.
        """
        pin_num = 20  # Default to GPIO20
        if self._speaker_device is not None:
            return self._speaker_device
        try:
            self.get_logger().info(
                f"Initializing speaker Pin on pin {pin_num} (PinMode.OUT)"
            )
            self._speaker_device = Pin(pin_num, mode=PinMode.OUT)
        except Exception as e:
            self.get_logger().error(f"Failed to initialize speaker Pin: {e}")
            self._speaker_device = None
        return self._speaker_device

    def _enable_speaker(self):
        self.get_logger().debug("Setting speaker GPIO HIGH (enable speaker).")
        device = self._get_speaker_device()
        if device is not None:
            try:
                device.on()
                self.get_logger().debug("Speaker pin set HIGH.")
            except Exception as e:
                self.get_logger().warn(f"Failed to enable speaker: {e}")

    def _disable_speaker(self):
        self.get_logger().debug("Setting speaker GPIO LOW (disable speaker).")
        device = self._get_speaker_device()
        if device is not None:
            try:
                device.off()
            except Exception as e:
                self.get_logger().warn(f"Failed to disable speaker: {e}")

def main(args=None):
    """
    Entry point for the node.
    Initializes ROS 2, creates the node, and spins.

    Handles:
        - KeyboardInterrupt: Gracefully shuts down the node on user interruption.
        - Other exceptions: Logs the error and shuts down the node.
    """
    rclpy.init(args=args)
    node = None
    try:
        node = PicarxSpeakDetectionsNode()
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


if __name__ == "__main__":
    main()
