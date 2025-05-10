import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from robot_hat import Pin, Ultrasonic
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device


class PicarxUltrasonicPublisher(Node):
    """
    A ROS2 node that publishes ultrasonic sensor readings to a topic.
    """

    def __init__(self) -> None:
        """
        Initializes the PicarxUltrasonicPublisher node, sets up the ultrasonic sensor,
        and starts a timer to periodically publish sensor data.
        """
        super().__init__("picarx_ultrasonic_node")

        self.publisher = self.create_publisher(Range, "picarx/ultrasonic_sensor", 10)
        try:
            Device.pin_factory = LGPIOFactory()
            self.get_logger().info("LGPIOFactory initialized successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize LGPIOFactory: {e}")
        try:
            trig_pin = self.declare_parameter(
                "trig_pin", "D2", descriptor=rclpy.parameter.ParameterDescriptor(description="GPIO pin for the ultrasonic sensor trigger")
            ).value
            echo_pin = self.declare_parameter(
                "echo_pin", "D3", descriptor=rclpy.parameter.ParameterDescriptor(description="GPIO pin for the ultrasonic sensor echo")
            ).value

            self.ultrasonic_sensor = Ultrasonic(
                trig=Pin(trig_pin), echo=Pin(echo_pin), timeout=0.055
            )
            self.get_logger().info(
                f"Ultrasonic sensor initialized with trig={trig_pin}, echo={echo_pin}."
            )
        except Exception as e:
            self.get_logger().error(f"Failed to initialize Ultrasonic sensor: {e}")
            self.ultrasonic_sensor = None

        if self.ultrasonic_sensor is None:
            self.get_logger().error("Ultrasonic sensor initialization failed. Shutting down the node.")
            rclpy.shutdown()
            self.get_logger().info("Node shutdown complete.")
            return

        timer_period = self.declare_parameter(
            "timer_period", 1.0, descriptor=rclpy.parameter.ParameterDescriptor(description="Timer period for publishing sensor data (in seconds)")
        ).value
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info("Picarx Ultrasonic Publisher has been started.")

    def timer_callback(self):
        # Log the received values
        if self.ultrasonic_sensor is None:
            self.get_logger().error("Ultrasonic sensor is not initialized.")
            return

        try:
            range = self.ultrasonic_sensor.read()
        except Exception as e:
            self.get_logger().error(f"Error reading from ultrasonic sensor: {e}")
            return

        # Publish a status message
        if range > 0:
            range = range / 100.0  # Convert from cm to meters
            self.get_logger().debug(f"Range: {range} meters")
            range_msg = Range()
            range_msg.header.stamp = self.get_clock().now().to_msg()
            range_msg.radiation_type = Range.ULTRASOUND
            range_msg.min_range = 0.02  # Minimum range in meters
            range_msg.max_range = 5.0  # Maximum range in meters
            range_msg.range = range
            self.publisher.publish(range_msg)
        elif range == -1:
            self.get_logger().debug("Ultrasonic sensor reading error.")
        elif range == -2:
            self.get_logger().debug("Ultrasonic sensor pulse error.")

    def destroy_node(self):
        self.get_logger().info("Shutting down Picarx Ultrasonic Publisher.")
        if self.ultrasonic_sensor:
            try:
                self.ultrasonic_sensor.close()
                self.get_logger().info("Ultrasonic sensor closed successfully.")
            except Exception as e:
                self.get_logger().error(f"Failed to close Ultrasonic sensor: {e}")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PicarxUltrasonicPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
