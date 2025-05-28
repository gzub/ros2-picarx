"""
Picarx Grayscale Node for SunFounder PiCarX (Robot Hat v4, ROS 2 Kilted).

This node interfaces with the SunFounder Grayscale_Module (which uses a TCRT5000) via the Robot Hat v4,
publishes raw grayscale sensor data, and publishes line status changes.
It is designed for use on Raspberry Pi OS (Pi 5) and is compatible with the
SunFounder PiCarX hardware and ROS 2 conventions.

References:
- https://docs.sunfounder.com/projects/picar-x-v20/en/latest/
- https://docs.sunfounder.com/projects/robot-hat-v4/en/latest/
- https://docs.ros.org/en/rolling/
"""

import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Illuminance
from std_msgs.msg import Int32MultiArray

from picarx.robot_hat_interface import ADC, GrayscaleModule


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

        # Declare parameters for ADC pins, reference values, frame, and frequency
        self.declare_parameter("adc_pins", [0, 1, 2])
        self.declare_parameter("reference_values", [750, 750, 750])
        self.declare_parameter("frame_id", "grayscale_link")
        self.declare_parameter("frequency", 20.0)  # Default: 20 Hz

        # Get parameters
        adc_pins = (
            self.get_parameter("adc_pins").get_parameter_value().integer_array_value
        )
        reference_values = (
            self.get_parameter("reference_values")
            .get_parameter_value()
            .integer_array_value
        )
        self.frame_id = (
            self.get_parameter("frame_id").get_parameter_value().string_value
        )

        # Initialize the Grayscale Module
        try:
            self.grayscale_module = GrayscaleModule(
                pin0=ADC(adc_pins[0]),
                pin1=ADC(adc_pins[1]),
                pin2=ADC(adc_pins[2]),
                reference=reference_values,
                logger=self.get_logger(),
            )
            self.get_logger().info(
                f"Grayscale Module initialized with pins {adc_pins} and reference {reference_values}."
            )
        except Exception as e:
            self.get_logger().error(f"Failed to initialize Grayscale Module: {e}")
            rclpy.shutdown()
            return

        # Publisher for each grayscale sensor as Illuminance
        self.illuminance_publishers = [
            self.create_publisher(
                Illuminance, f"/grayscale_sensor_{i}", qos_profile_sensor_data
            )
            for i in range(3)
        ]

        # Publisher for line status
        self.line_status_publisher = self.create_publisher(
            Int32MultiArray, "/line_status", qos_profile_sensor_data
        )

        # Initialize threading lock
        self.lock = threading.Lock()

        # Initialize previous line status
        self.previous_line_status = None

        # Timer to periodically read and publish data
        frequency = self.get_parameter("frequency").get_parameter_value().double_value
        if frequency <= 0.0:
            self.get_logger().warn("frequency must be > 0. Using 20.0 Hz.")
            frequency = 20.0
        timer_period = 1.0 / frequency
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        """
        Timer callback to read data from the Grayscale Module and publish it.

        Reads grayscale data, publishes it, checks for line status changes,
        and publishes line status if it has changed.
        """
        # Only hold the lock for hardware access and updating shared state
        try:
            with self.lock:
                grayscale_data = self.read_grayscale_data()
                self.get_logger().debug(f"Grayscale sensor values: {grayscale_data}")
                self.publish_illuminance(grayscale_data)

                line_status = self.read_line_status(grayscale_data)
            # Publish line status outside the lock to avoid holding the lock during publish
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

    def publish_illuminance(self, grayscale_data):
        """
        Publishes each grayscale sensor value as an Illuminance message.

        Args:
            grayscale_data (list): The grayscale sensor readings.
        """
        # Only lock if accessing shared state (not needed here, as no shared state is modified)
        if len(grayscale_data) != 3:
            self.get_logger().warn(
                f"Expected 3 grayscale values, got {len(grayscale_data)}"
            )
            return
        for i, value in enumerate(grayscale_data):
            try:
                msg = Illuminance()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = f"{self.frame_id}_{i}"
                msg.illuminance = float(value)
                msg.variance = 0.0
                self.illuminance_publishers[i].publish(msg)
            except IndexError:
                self.get_logger().error(
                    f"Sensor index {i} out of range for publishers."
                )

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
        # Use lock only for accessing/modifying previous_line_status
        with self.lock:
            if not isinstance(line_status, list) or len(line_status) != 3:
                self.get_logger().warn(
                    f"Expected 3 line status values, got {line_status}"
                )
                return
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
    node = None
    try:
        node = PicarxGrayscaleNode()
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
