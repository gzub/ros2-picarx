"""
Picarx Speak Detections Node

This ROS 2 node subscribes to the /camera/detections topic (vision_msgs/Detection2DArray),
extracts detected object labels, and uses the Raspberry Pi speaker to announce what was detected.
It uses espeak for speech synthesis and the robot_hat package to enable/disable the speaker.

Compatible with Raspberry Pi OS, PiCarX, and Robot Hat v4.
"""

import subprocess

import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray

from robot_hat.utils import disable_speaker, enable_speaker


class PicarxSpeakDetectionsNode(Node):
    """
    Node that speaks detected objects using the onboard speaker.
    """

    def __init__(self):
        super().__init__("picarx_speak_detections_node")
        self.subscription = self.create_subscription(
            Detection2DArray, "/camera/detections", self.detection_callback, 10
        )
        self.last_spoken = set()
        self.get_logger().info("PicarxSpeakDetectionsNode started.")

    def detection_callback(self, msg: Detection2DArray):
        detected_labels = set()
        for detection in msg.detections:
            if detection.results:
                label = detection.results[0].hypothesis.class_id
                detected_labels.add(label)
        if not detected_labels:
            return

        # Only speak new detections
        new_labels = detected_labels - self.last_spoken
        if not new_labels:
            return

        phrase = "I see a " + ", ".join(new_labels)
        self.get_logger().info(f"Speaking: {phrase}")

        try:
            enable_speaker()
            subprocess.run(["espeak", phrase], check=True)
        except Exception as e:
            self.get_logger().error(f"Failed to speak: {e}")
        finally:
            disable_speaker()
        self.last_spoken = detected_labels


def main(args=None):
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
        rclpy.shutdown()


if __name__ == "__main__":
    main()
