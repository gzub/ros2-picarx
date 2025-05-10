import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from sensor_msgs.msg import Range
from robot_hat import ADC, Grayscale_Module


class PicarxGrayscaleNode(Node):
    """
    A ROS 2 node that interfaces with the Grayscale_Module and publishes its data.
    """

    def __init__(self):
        super().__init__("picarx_grayscale_node")
        self.get_logger().info("Picarx Grayscale Node has been started.")

        # Declare parameters for ADC pins and reference values
        self.declare_parameter("adc_pins", [0, 1, 2])  # Default ADC pins
        self.declare_parameter("reference_values", [500, 500, 500])  # Default reference values

        # Get parameters
        adc_pins = self.get_parameter("adc_pins").get_parameter_value().integer_array_value
        reference_values = self.get_parameter("reference_values").get_parameter_value().integer_array_value

        # Initialize the Grayscale Module
        try:
            self.grayscale_module = Grayscale_Module(
                pin0=ADC(adc_pins[0]),
                pin1=ADC(adc_pins[1]),
                pin2=ADC(adc_pins[2]),
                reference=reference_values
            )
            self.get_logger().info(f"Grayscale Module initialized with pins {adc_pins} and reference {reference_values}.")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize Grayscale Module: {e}")
            rclpy.shutdown()
            return

        # Publisher for grayscale data
        self.grayscale_publisher = self.create_publisher(Int32MultiArray, "picarx/grayscale_data", 10)

        # Publisher for line status
        self.line_status_publisher = self.create_publisher(Int32MultiArray, "picarx/line_status", 10)

        # Timer to periodically read and publish data
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 Hz

    def timer_callback(self):
        """
        Timer callback to read data from the Grayscale Module and publish it.
        """
        try:
            # Read grayscale data
            grayscale_data = self.grayscale_module.read()
            grayscale_msg = Int32MultiArray()
            grayscale_msg.data = grayscale_data
            self.grayscale_publisher.publish(grayscale_msg)

            # Read line status
            line_status = self.grayscale_module.read_status(grayscale_data)
            line_status_msg = Int32MultiArray()
            line_status_msg.data = line_status
            self.line_status_publisher.publish(line_status_msg)

            self.get_logger().debug(f"Published grayscale data: {grayscale_data}")
            self.get_logger().debug(f"Published line status: {line_status}")
        except Exception as e:
            self.get_logger().error(f"Error reading from Grayscale Module: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = PicarxGrayscaleNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()