"""
Picarx Ultrasonic Node for SunFounder PiCarX (Robot Hat v4, ROS 2 Jazzy).

This node interfaces with the SunFounder Ultrasonic sensor via the Robot Hat v4,
publishes filtered range data to a ROS 2 topic, and supports configuration of
minimum/maximum range and hysteresis filtering. Designed for Raspberry Pi OS on
Raspberry Pi 5 and compatible with SunFounder PiCarX hardware.

References:
- https://docs.sunfounder.com/projects/picar-x-v20/en/latest/
- https://docs.sunfounder.com/projects/robot-hat-v4/en/latest/
- https://docs.ros.org/en/rolling/
"""

import threading

import rclpy
from gpiozero import Device
from gpiozero.pins.lgpio import LGPIOFactory
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Range
from rcl_interfaces.msg import ParameterDescriptor, ParameterType

from robot_hat import Pin, Ultrasonic

# Move valid_pins to module-level constant for clarity
VALID_PICARX_PINS = {"D0", "D1", "D2", "D3"}


class PicarxUltrasonicPublisher(Node):
    """
    A ROS 2 node that publishes ultrasonic sensor readings to a topic.

    This node reads distance measurements from the SunFounder Ultrasonic sensor,
    applies a hysteresis filter to reduce noise, and publishes the filtered
    range data as sensor_msgs/Range messages.
    """

    def __init__(self) -> None:
        """
        Initializes the PicarxUltrasonicPublisher node, sets up the ultrasonic sensor,
        declares parameters, and starts a timer to periodically publish sensor data.
        """
        super().__init__("picarx_ultrasonic_node")

        self.lock = threading.Lock()
        self.previous_range = None

        # Declare parameters for timer period, min range, max range, and hysteresis threshold
        timer_period = self.declare_parameter(
            "timer_period",
            1.0,
            ParameterDescriptor(type=ParameterType.PARAMETER_DOUBLE),
        ).value
        self.min_range = self.declare_parameter(
            "min_range", 0.02, ParameterDescriptor(type=ParameterType.PARAMETER_DOUBLE)
        ).value
        self.max_range = self.declare_parameter(
            "max_range", 4.0, ParameterDescriptor(type=ParameterType.PARAMETER_DOUBLE)
        ).value
        self.field_of_view = self.declare_parameter(
            "field_of_view",
            0.2618,
            ParameterDescriptor(type=ParameterType.PARAMETER_DOUBLE),
        ).value
        self.sensor_timeout = self.declare_parameter(
            "sensor_timeout",
            0.055,
            ParameterDescriptor(type=ParameterType.PARAMETER_DOUBLE),
        ).value
        self.hysteresis_threshold = self.declare_parameter(
            "hysteresis_threshold",
            0.05,
            ParameterDescriptor(type=ParameterType.PARAMETER_DOUBLE),
        ).value
        trig_pin = self.declare_parameter(
            "trig_pin", "D2", ParameterDescriptor(type=ParameterType.PARAMETER_STRING)
        ).value
        echo_pin = self.declare_parameter(
            "echo_pin", "D3", ParameterDescriptor(type=ParameterType.PARAMETER_STRING)
        ).value

        self.get_logger().info(
            f"Parameters: trig_pin={trig_pin}, echo_pin={echo_pin}, "
            f"min_range={self.min_range}, max_range={self.max_range}, "
            f"field_of_view={self.field_of_view}, sensor_timeout={self.sensor_timeout}, "
            f"hysteresis_threshold={self.hysteresis_threshold}"
        )

        # Use module-level constant for valid pins
        invalid_pins = []
        if trig_pin not in VALID_PICARX_PINS:
            invalid_pins.append(f"trig_pin={trig_pin}")
        if echo_pin not in VALID_PICARX_PINS:
            invalid_pins.append(f"echo_pin={echo_pin}")
        if invalid_pins:
            self.get_logger().error(f"Invalid pin(s): {', '.join(invalid_pins)}")
            rclpy.shutdown()
            return

        self.publisher = self.create_publisher(
            Range, "picarx/ultrasonic_sensor", qos_profile_sensor_data
        )
        try:
            Device.pin_factory = LGPIOFactory()
            self.get_logger().info("LGPIOFactory initialized successfully.")
        except Exception as e:
            self.get_logger().error(
                f"Failed to initialize LGPIOFactory: {type(e).__name__}: {e}"
            )
        try:
            self.ultrasonic_sensor = Ultrasonic(
                trig=Pin(trig_pin), echo=Pin(echo_pin), timeout=self.sensor_timeout
            )
            self.get_logger().info(
                f"Ultrasonic sensor initialized with trig={trig_pin}, echo={echo_pin}."
            )
        except Exception as e:
            self.get_logger().error(
                f"Failed to initialize Ultrasonic sensor: {type(e).__name__}: {e}"
            )
            self.ultrasonic_sensor = None

        if self.ultrasonic_sensor is None:
            self.get_logger().error(
                "Ultrasonic sensor initialization failed. Shutting down the node."
            )
            rclpy.shutdown()
            return  # Ensure no further code is executed

        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.get_logger().info("Picarx Ultrasonic Publisher has been started.")

    def timer_callback(self) -> None:
        """
        Timer callback to read and publish filtered ultrasonic sensor data.

        Reads the current range from the ultrasonic sensor, applies a hysteresis
        filter to suppress small fluctuations, and publishes the filtered value
        as a sensor_msgs/Range message.
        """
        with self.lock:
            if self.ultrasonic_sensor is None:
                self.get_logger().error("Ultrasonic sensor is not initialized.")
                return

            try:
                range_ = self.ultrasonic_sensor.read()
                if range_ < 0 or range_ > (
                    self.max_range * 100
                ):  # Convert max_range to cm
                    self.get_logger().debug(f"Invalid range value: {range_} cm")
                    return
            except Exception as e:
                self.get_logger().error(
                    f"Error reading from ultrasonic sensor: {type(e).__name__}: {e}"
                )
                return

            # Apply hysteresis filter
            if range_ > 0:
                range_ = range_ / 100.0  # Convert from cm to meters
                if self.previous_range is None or abs(range_ - self.previous_range) > (
                    self.hysteresis_threshold * self.previous_range
                ):
                    self.previous_range = range_
                    self.get_logger().debug(f"Filtered Range: {range_} meters")
                    range_msg = Range()
                    range_msg.header.stamp = self.get_clock().now().to_msg()
                    range_msg.radiation_type = Range.ULTRASOUND
                    range_msg.field_of_view = self.field_of_view
                    range_msg.min_range = self.min_range  # Use parameterized min range
                    range_msg.max_range = self.max_range  # Use parameterized max range
                    range_msg.range = range_
                    range_msg.variance = 0.0
                    self.publisher.publish(range_msg)
                else:
                    self.get_logger().debug(
                        f"Range change below hysteresis threshold: {range_} meters"
                    )
            elif range_ == -1:
                self.get_logger().debug("Ultrasonic sensor reading error.")
            elif range_ == -2:
                self.get_logger().debug("Ultrasonic sensor pulse error.")

    def destroy_node(self) -> None:
        """
        Cleans up resources before shutting down the node.
        """
        self.get_logger().info("Shutting down Picarx Ultrasonic Publisher.")
        super().destroy_node()


def main(args=None):
    """
    Main entry point for the PicarxUltrasonicPublisher node.

    Initializes the ROS 2 node, spins it to process incoming messages, and
    ensures proper cleanup during shutdown.
    """

    rclpy.init(args=args)
    node = None
    try:
        node = PicarxUltrasonicPublisher()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info("Shutting down...")
    except Exception as e:
        if node:
            node.get_logger().error(f"Unhandled exception: {e}")

        rclpy.shutdown()


if __name__ == "__main__":
    main()
