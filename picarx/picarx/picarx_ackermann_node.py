"""
Picarx Ackermann Node for SunFounder PiCarX (Robot Hat v4, ROS 2 Jazzy).

This node subscribes to AckermannDrive messages and controls the PiCarX robot's
motors and steering servo using the Robot Hat v4 hardware interface. It computes
the correct left and right motor speeds for Ackermann steering, ensuring that
the inside wheel slows down during turns and that neither motor exceeds the
configured maximum speed. The node is designed for Raspberry Pi OS on Raspberry Pi 5
and is compatible with SunFounder PiCarX hardware and ROS 2 conventions.

References:
- https://docs.sunfounder.com/projects/picar-x-v20/en/latest/
- https://docs.sunfounder.com/projects/robot-hat-v4/en/latest/
- https://docs.ros.org/en/rolling/
"""

import threading
import math
import time

import rclpy
from gpiozero import Device
from gpiozero.pins.lgpio import LGPIOFactory
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from ackermann_msgs.msg import AckermannDrive, AckermannDriveStamped
from robot_hat import PWM, Motor, Pin, Servo


class PicarxAckermann(Node):
    """
    A ROS 2 node for controlling a Picar-X robot using Ackermann steering.

    This node subscribes to AckermannDrive messages to control the speed and
    steering angle of the robot. It calculates the motor speeds for the left
    and right wheels based on the Ackermann steering model and ensures that
    the motor speeds do not exceed the maximum speed.
    """

    def __init__(self):
        """
        Initializes the PicarxAckermann node.

        Sets up the ROS 2 subscription and publisher, declares parameters,
        initializes hardware, and sets up threading for safe access to shared
        resources.
        """
        super().__init__("picarx_ackermann_node")

        # Initialize a threading lock
        self.lock = threading.Lock()
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.subscription = self.create_subscription(
            AckermannDrive, "picarx/cmd_ackermann", self.listener_callback, qos_profile
        )
        self.publisher = self.create_publisher(
            AckermannDriveStamped, "picarx/robot_status", qos_profile
        )

        self.declare_and_get_parameters()

        self.initialize_hardware()

        self.current_speed = 0.0
        self.current_angle = 0.0

        self.last_cmd_time = time.monotonic()
        self.cmd_timeout = 0.5  # seconds
        self.watchdog_timer = self.create_timer(0.1, self.watchdog_callback)

        self.get_logger().info("Picarx Ackermann node has been started.")

    def declare_and_get_parameters(self):
        """
        Declares and retrieves parameters for the node.

        Parameters include:
        - max_speed: Maximum speed of the robot.
        - max_steering_angle: Maximum steering angle of the robot.
        - steering_angle_offset: Offset to apply to the steering angle.
        - motor_0_pwm_pin: PWM pin for motor 0.
        - motor_0_dir_pin: Direction pin for motor 0.
        - motor_1_pwm_pin: PWM pin for motor 1.
        - motor_1_dir_pin: Direction pin for motor 1.
        - servo_pin: Pin for the servo controlling the steering.
        - wheelbase: Distance between the front and rear axles (in meters).
        - track_length: Distance between the left and right wheels (in meters).
        """
        self.declare_parameter("max_speed", 100.0)
        self.declare_parameter("max_steering_angle", 45.0)
        self.declare_parameter("steering_angle_offset", -10.5)
        self.declare_parameter("motor_0_pwm_pin", "P12")
        self.declare_parameter("motor_0_dir_pin", "D5")
        self.declare_parameter("motor_1_pwm_pin", "P13")
        self.declare_parameter("motor_1_dir_pin", "D4")
        self.declare_parameter("servo_pin", 2)
        self.declare_parameter(
            "wheelbase", 0.4
        )  # Distance between front and rear axles (in meters)
        self.declare_parameter(
            "track_length", 0.3
        )  # Distance between left and right wheels (in meters)

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
        self.motor_0_pwm_pin = (
            self.get_parameter("motor_0_pwm_pin").get_parameter_value().string_value
        )
        self.motor_0_dir_pin = (
            self.get_parameter("motor_0_dir_pin").get_parameter_value().string_value
        )
        self.motor_1_pwm_pin = (
            self.get_parameter("motor_1_pwm_pin").get_parameter_value().string_value
        )
        self.motor_1_dir_pin = (
            self.get_parameter("motor_1_dir_pin").get_parameter_value().string_value
        )
        self.servo_pin = (
            self.get_parameter("servo_pin").get_parameter_value().integer_value
        )
        self.wheelbase = (
            self.get_parameter("wheelbase").get_parameter_value().double_value
        )
        self.track_length = (
            self.get_parameter("track_length").get_parameter_value().double_value
        )

    def initialize_hardware(self):
        """
        Initializes the hardware components of the robot.

        This includes the motors and the servo for steering. The hardware
        is initialized using the pins specified in the parameters.
        """
        try:
            Device.pin_factory = LGPIOFactory()
            self.m0 = Motor(
                PWM(self.motor_1_pwm_pin), Pin(self.motor_1_dir_pin), is_reversed=True
            )
            self.m1 = Motor(PWM(self.motor_0_pwm_pin), Pin(self.motor_0_dir_pin))
            self.s0 = Servo(self.servo_pin)

            self.m0.speed(0.0)
            self.m1.speed(0.0)
            self.s0.angle(self.steering_angle_offset)

            self.get_logger().info("Hardware initialized successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize hardware: {e}")
            raise

    def listener_callback(self, msg):
        """
        Callback to handle incoming AckermannDrive messages.

        This method calculates the motor speeds for the left and right wheels
        based on the Ackermann steering model. It ensures that the motor speeds
        do not exceed the maximum speed and updates the hardware accordingly.

        Args:
            msg (AckermannDrive): The incoming AckermannDrive message.
        """
        with self.lock:
            self.last_cmd_time = time.monotonic()
            self.get_logger().debug(
                f"Picarx Ackermann node received a message: {msg.speed}, {msg.steering_angle}"
            )
            speed = max(min(msg.speed, self.max_speed), -self.max_speed)
            steering_angle = max(
                min(msg.steering_angle, self.max_steering_angle),
                -self.max_steering_angle,
            )

            # Calculate turning radius
            if steering_angle != 0:
                turning_radius = self.wheelbase / math.tan(math.radians(steering_angle))
                self.get_logger().debug(f"Turning radius: {turning_radius:.2f} meters")

                # Adjust motor speeds for Ackermann steering
                right_speed = (
                    speed * (turning_radius - self.track_length / 2) / turning_radius
                )
                left_speed = (
                    speed * (turning_radius + self.track_length / 2) / turning_radius
                )
            else:
                # Straight driving
                left_speed = speed
                right_speed = speed

            # Normalize motor speeds to ensure they do not exceed max_speed
            max_motor_speed = max(abs(left_speed), abs(right_speed))
            if max_motor_speed > self.max_speed:
                scaling_factor = self.max_speed / max_motor_speed
                left_speed *= scaling_factor
                right_speed *= scaling_factor

            if speed:
                self.get_logger().debug(
                    f"Commanded Speed: {speed:.2f}, Left speed: {left_speed:.2f}, Right speed: {right_speed:.2f}, Steering Angle: {steering_angle:.2f}"
                )

            # Update motors and servo
            self.s0.angle(steering_angle + self.steering_angle_offset)
            self.m0.speed(left_speed)
            self.m1.speed(right_speed)
            self.current_speed = speed
            self.current_angle = steering_angle

            # Publish a status message
            status_msg = AckermannDriveStamped()
            status_msg.header.stamp = self.get_clock().now().to_msg()
            status_msg.drive.speed = (left_speed + right_speed) / 2.0
            status_msg.drive.steering_angle = steering_angle
            self.publisher.publish(status_msg)

    def watchdog_callback(self):
        """
        Watchdog callback to stop the motors if no command is received within the timeout period.

        This method ensures the robot stops moving for safety if no command is received.
        """
        if time.monotonic() - self.last_cmd_time > self.cmd_timeout:
            if self.current_speed != 0.0 or self.current_angle != 0.0:
                self.get_logger().warn("No command received: stopping motors for safety.")
                self.m0.speed(0)
                self.m1.speed(0)
                self.s0.angle(self.steering_angle_offset)
                self.current_speed = 0.0
                self.current_angle = 0.0

    def stop_motors(self):
        """
        Stops the motors and resets the servo.

        This method is called during shutdown to ensure that the robot stops
        moving and the servo is reset to its default position.
        """
        self.m0.speed(0)
        self.m1.speed(0)
        self.s0.angle(self.steering_angle_offset)

    def destroy_node(self):
        """
        Cleans up resources before shutting down the node.

        This method stops the motors and resets the servo before calling the
        parent class's destroy_node method.
        """
        self.get_logger().info("Shutting down Picarx Ackermann Node.")
        self.stop_motors()
        super().destroy_node()


def main(args=None):
    """
    Main entry point for the Picarx Ackermann node.

    Initializes the ROS 2 node, spins it to process incoming messages, and
    ensures proper cleanup during shutdown.
    """
    rclpy.init(args=args)
    node = None
    try:
        node = PicarxAckermann()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info("Shutting down...")
    except Exception as e:
        if node:
            node.get_logger().error(f"Unhandled exception: {e}")
    finally:
        if node:
            node.stop_motors()
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
