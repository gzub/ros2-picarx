"""
Picarx Grayscale Node for SunFounder PiCarX (Robot Hat v4, ROS 2 Jazzy).

This node interfaces with the SunFounder Grayscale_Module via the Robot Hat v4,
publishes raw grayscale sensor data, and publishes line status changes.
It is designed for use on Raspberry Pi OS (Pi 5) and is compatible with the
SunFounder PiCarX hardware and ROS 2 conventions.

References:
- https://docs.sunfounder.com/projects/picar-x-v20/en/latest/
- https://docs.sunfounder.com/projects/robot-hat-v4/en/latest/
- https://docs.ros.org/en/rolling/
"""

import threading
from logging import getLogger

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import Int32MultiArray

from robot_hat import ADC, Grayscale_Module


class PicarxGrayscaleNode(Node):
    """
    A ROS 2 node that interfaces with the Grayscale_Module and publishes its data.

    This node reads grayscale sensor values from the SunFounder Robot Hat v4,
    publishes the raw grayscale data, and publishes line status changes.
    """

    def __init__(self):
        """
        Initialize the PicarxGrayscaleNode.

        Sets up publishers, parameters, hardware interface, and a periodic timer.
        """
        super().__init__("picarx_grayscale_node")
        self.get_logger().info("Picarx Grayscale Node has been started.")

        # Declare parameters for ADC pins and reference values
        self.declare_parameter("adc_pins", [0, 1, 2])  # Default ADC pins
        self.declare_parameter(
            "reference_values", [750, 750, 750]
        )  # Default reference values

        # Get parameters
        adc_pins = (
            self.get_parameter("adc_pins").get_parameter_value().integer_array_value
        )
        reference_values = (
            self.get_parameter("reference_values")
            .get_parameter_value()
            .integer_array_value
        )

        # Initialize the Grayscale Module
        try:
            self.grayscale_module = Grayscale_Module(
                pin0=ADC(adc_pins[0]),
                pin1=ADC(adc_pins[1]),
                pin2=ADC(adc_pins[2]),
                reference=reference_values,
            )
            self.get_logger().info(
                f"Grayscale Module initialized with pins {adc_pins} and reference {reference_values}."
            )
        except Exception as e:
            self.get_logger().error(f"Failed to initialize Grayscale Module: {e}")
            rclpy.shutdown()
            return

        # Publisher for grayscale data
        self.grayscale_publisher = self.create_publisher(
            Int32MultiArray, "picarx/grayscale_data", qos_profile_sensor_data
        )

        # Publisher for line status
        self.line_status_publisher = self.create_publisher(
            Int32MultiArray, "picarx/line_status", qos_profile_sensor_data
        )

        # Initialize threading lock
        self.lock = threading.Lock()

        # Initialize previous line status
        self.previous_line_status = None

        # Timer to periodically read and publish data
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 Hz

    def timer_callback(self):
        """
        Timer callback to read data from the Grayscale Module and publish it.

        Reads grayscale data, publishes it, checks for line status changes,
        and publishes line status if it has changed.
        """
        with self.lock:
            try:
                grayscale_data = self.read_grayscale_data()
                self.publish_grayscale_data(grayscale_data)

                line_status = self.read_line_status(grayscale_data)
                self.publish_line_status(line_status)
            except Exception as e:
                self.get_logger().error(f"Error in timer callback: {e}")

    def read_grayscale_data(self):
        """
        Reads grayscale data from the Grayscale Module.

        Returns:
            list: The grayscale sensor readings.
        """
        try:
            return self.grayscale_module.read()
        except Exception as e:
            self.get_logger().error(f"Failed to read grayscale data: {e}")
            return []

    def publish_grayscale_data(self, grayscale_data):
        """
        Publishes grayscale data to the corresponding topic.

        Args:
            grayscale_data (list): The grayscale sensor readings.
        """
        grayscale_msg = Int32MultiArray()
        grayscale_msg.data = grayscale_data
        self.grayscale_publisher.publish(grayscale_msg)

    def read_line_status(self, grayscale_data):
        """
        Reads line status based on the grayscale data.

        Args:
            grayscale_data (list): The grayscale sensor readings.

        Returns:
            list: The line status derived from the grayscale data.
        """
        try:
            return self.grayscale_module.read_status(grayscale_data)
        except Exception as e:
            self.get_logger().error(f"Failed to read line status: {e}")
            return []

    def publish_line_status(self, line_status):
        """
        Publishes line status to the corresponding topic if it has changed.

        Args:
            line_status (list): The current line status.
        """
        if self.previous_line_status != line_status:
            line_status_msg = Int32MultiArray()
            line_status_msg.data = line_status
            self.line_status_publisher.publish(line_status_msg)
            self.previous_line_status = line_status

    def destroy_node(self):
        """
        Cleans up resources before shutting down the node.
        """
        self.get_logger().info("Shutting down Picarx Grayscale Node.")
        super().destroy_node()


def main(args=None):
    """
    Main entry point for the PicarxGrayscaleNode.

    Initializes the ROS 2 node, spins it to process incoming messages, and
    ensures proper cleanup during shutdown.
    """
    rclpy.init(args=args)
    try:
        node = PicarxGrayscaleNode()
        rclpy.spin(node)
    except Exception as e:
        getLogger().error("Unhandled exception: %s", e)
    finally:
        if "node" in locals():
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
