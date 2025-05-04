from time import sleep
import rclpy
from rclpy.node import Node
from ackermann_msgs.msg import AckermannDrive, AckermannDriveStamped
from robot_hat import Motor, PWM, Pin, Servo
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device


class PicarxAckermann(Node):
    """
    A ROS 2 node for controlling a Picar-X robot using Ackermann steering.
    """

    def __init__(self):
        super().__init__("picarx_node")

        self.subscription = self.create_subscription(
            AckermannDrive, "picarx/cmd_ackermann", self.listener_callback, 10
        )
        self.publisher = self.create_publisher(
            AckermannDriveStamped, "picarx/robot_status", 10
        )
        # Declare parameters for limits and calibration
        self.declare_parameter("max_speed", 100.0)  # Maximum speed
        self.declare_parameter(
            "max_steering_angle", 45.0
        )  # Maximum steering angle in degrees
        self.declare_parameter(
            "steering_angle_offset", -4.5
        )  # Calibration offset for steering angle
        self.max_speed = (
            self.get_parameter("max_speed").get_parameter_value().double_value
        )
        self.max_steering_angle = (
            self.get_parameter("max_steering_angle").get_parameter_value().double_value
        )
        self.steering_angle_offset = (
            self.get_parameter("steering_angle_offset")
            .get_parameter_value()
            .double_value
        )
        try:
            Device.pin_factory = LGPIOFactory()
            print("LGPIOFactory initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize LGPIOFactory: {e}")
        try:
            self.m0 = Motor(PWM("P12"), Pin("D5"))
            self.m1 = Motor(PWM("P13"), Pin("D4"), is_reversed=True)
            self.s2 = Servo(2)
            self.m0.speed(0)
            self.m1.speed(0)
            self.s2.angle(self.steering_angle_offset)
        except Exception as e:
            self.get_logger().error(f"Failed to initialize motors or servos: {e}")
            raise

        self.current_speed = 0
        self.current_angle = 0

        self.get_logger().info("Picarx Ackermann node has been started.")

    def listener_callback(self, msg):
        speed = max(min(msg.speed, self.max_speed), -self.max_speed)
        steering_angle = max(
            min(msg.steering_angle, self.max_steering_angle), -self.max_steering_angle
        )

        # Apply the steering angle offset
        steering_angle += self.steering_angle_offset

        if steering_angle != self.current_angle:
            self.s2.angle(steering_angle)
            self.current_angle = steering_angle

        if speed != self.current_speed:
            self.m0.speed(speed)
            self.m1.speed(speed)
            self.current_speed = speed

        # Publish a status message
        status_msg = AckermannDriveStamped()
        status_msg.header.stamp = self.get_clock().now().to_msg()  # Add timestamp
        status_msg.drive.speed = (
            self.m0.speed() + self.m1.speed()
        ) / 2.0  # Assuming both motors are set to the same speed
        status_msg.drive.steering_angle = steering_angle
        self.publisher.publish(status_msg)


def main(args=None):
    rclpy.init(args=args)
    node = PicarxAckermann()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info("Shutting down, stopping motors...")
        try:
            node.m0.speed(0)
            node.m1.speed(0)
            node.s2.angle(0)
        except Exception as e:
            node.get_logger().error(f"Failed to stop motors or servos: {e}")
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
