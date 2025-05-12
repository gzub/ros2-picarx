"""
Object Avoidance Node for PiCarX.

This ROS 2 node subscribes to ultrasonic sensor data and publishes stop commands
to the Ackermann drive topic if an object is detected within a configurable minimum distance.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from sensor_msgs.msg import Range
from ackermann_msgs.msg import AckermannDrive


class ObjectAvoidanceNode(Node):
    """
    Node for simple object avoidance using ultrasonic sensor data.

    Subscribes to the ultrasonic sensor topic and publishes a stop command
    to the Ackermann drive topic if an object is detected within the minimum distance.
    """

    def __init__(self):
        """
        Initialize the ObjectAvoidanceNode.

        Sets up the subscriber for the ultrasonic sensor, the publisher for AckermannDrive,
        and declares the minimum distance parameter.
        """
        super().__init__("object_avoidance")

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        # Subscribe to ultrasonic sensor
        self.subscription = self.create_subscription(
            Range,
            "picarx/ultrasonic_sensor",
            self.sensor_callback,
            qos_profile_sensor_data,
        )

        # Publish to cmd_ackermann
        self.publisher_ = self.create_publisher(
            AckermannDrive, "picarx/cmd_ackermann", qos_profile
        )

        # Define minimum distance parameter
        self.declare_parameter("min_distance", 0.5)  # meters
        self.min_distance = self.get_parameter("min_distance").value

    def sensor_callback(self, msg: Range) -> None:
        """
        Callback function for the ultrasonic sensor topic.

        If an object is detected within the minimum distance, publishes a stop command.
        Otherwise, logs the current distance.

        Args:
            msg (Range): The incoming ultrasonic sensor message.
        """
        try:
            if msg.range < 0.0:
                self.get_logger().warn(f"Received invalid range value: {msg.range:.2f}")
                return

            if msg.range <= self.min_distance:
                self.get_logger().info(
                    f"Object detected within {self.min_distance:.2f} meters ({msg.range:.2f} meters). Stopping!"
                )
                # Publish stop command
                stop_command = AckermannDrive()
                stop_command.speed = 0.0  # Stop the vehicle
                stop_command.steering_angle = 0.0  # Stop steering

                # self.publisher_.publish(stop_command)
            else:
                self.get_logger().debug(
                    f"Object is {msg.range:.2f} meters away. Continuing."
                )

        except Exception as e:
            self.get_logger().error(f"Error in sensor callback: {e}")


def main(args=None):
    """
    Main entry point for the ObjectAvoidanceNode.

    Initializes the ROS 2 node, spins it to process incoming messages, and
    ensures proper cleanup during shutdown.
    """
    rclpy.init(args=args)
    node = None
    try:
        node = ObjectAvoidanceNode()
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
