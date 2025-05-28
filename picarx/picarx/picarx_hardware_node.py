"""
Picarx hardware Node for SunFounder PiCarX (Robot Hat v4, ROS 2 Jazzy).

This node subscribes to JointState messages (from topic_based_ros2_control or compatible controllers)
and controls the PiCarX robot's motors and steering servo using the Robot Hat v4 hardware interface.
It computes the correct left and right motor speeds and steering angle, ensuring safe operation.
The node is designed for Raspberry Pi OS on Raspberry Pi 5 and is compatible with SunFounder PiCarX hardware and ROS 2 conventions.

References:
- https://docs.sunfounder.com/projects/picar-x-v20/en/latest/
- https://docs.sunfounder.com/projects/robot-hat-v4/en/latest/
- https://docs.ros.org/en/rolling/
"""

import math
import threading
import time

import rclpy
import sensor_msgs
from gpiozero import Device
from gpiozero.pins.lgpio import LGPIOFactory
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import JointState

from picarx.robot_hat_interface import DirectI2CMotor, DirectI2CServo


class PicarxHardware(Node):
    """
    ROS 2 node for controlling PiCarX using ros2_control joint commands.

    Subscribes to joint command messages and translates them to hardware actions
    for the PiCarX robot (motors and steering servo). Publishes joint states.
    Handles parameter management, hardware initialization, and safe shutdown.
    """

    def __init__(self):
        """
        Initializes the PicarxHardware node.

        Sets up the ROS 2 subscription and publisher, declares parameters,
        initializes hardware, and sets up threading for safe access to shared
        resources.
        """
        super().__init__("picarx_hardware_node")

        # Initialize a threading lock
        self.lock = threading.Lock()

        # Subscribe to topic_based_ros2_control joint commands
        self.joint_cmd_sub = self.create_subscription(
            sensor_msgs.msg.JointState,
            "/robot_joint_commands",
            self.joint_command_callback,
            QoSProfile(
                reliability=ReliabilityPolicy.RELIABLE,
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
            ),
        )

        self.joint_state_pub = self.create_publisher(
            JointState,
            "/robot_joint_states",
            QoSProfile(
                reliability=ReliabilityPolicy.BEST_EFFORT,
                history=HistoryPolicy.KEEP_LAST,
                depth=10,
            ),
        )

        self.declare_and_get_parameters()

        # Declare a parameter for frame_id with a default value
        self.declare_parameter("frame_id", "base_link")
        self.frame_id = (
            self.get_parameter("frame_id").get_parameter_value().string_value
        )

        self.initialize_hardware()

        self.current_speed = 0.0
        self.current_angle = 0.0

        self.last_cmd_time = time.monotonic()
        self.declare_parameter("cmd_timeout", 0.5)  # Default timeout is 0.5 seconds
        self.cmd_timeout = (
            self.get_parameter("cmd_timeout").get_parameter_value().double_value
        )

        self.last_published_state = None  # Track last published state

        self.last_steering_angle = 0.0
        self.last_left_speed = 0.0
        self.last_right_speed = 0.0

        self.get_logger().info(f"{self.get_name()} node (v1.0) has been started.")

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
        - servo_pwm_pin: Pin for the servo controlling the steering.
        - wheelbase: Distance between the front and rear axles (in meters).
        - track_length: Distance between the left and right wheels (in meters).
        """
        self.declare_parameter("max_speed", 25.0)
        self.declare_parameter("max_steering_angle", 45.0)
        self.declare_parameter("steering_angle_offset", -10.5)
        self.declare_parameter("motor_0_pwm_pin", 12)
        self.declare_parameter("motor_0_dir_pin", 24)
        self.declare_parameter("motor_1_pwm_pin", 13)
        self.declare_parameter("motor_1_dir_pin", 23)
        self.declare_parameter("servo_pwm_pin", 2)
        self.declare_parameter(
            "wheelbase", 0.4
        )  # Distance between front and rear axles (in meters)
        self.declare_parameter(
            "track_length", 0.3
        )  # Distance between left and right wheels (in meters)

        self.max_speed = (
            self.get_parameter("max_speed").get_parameter_value().double_value
        )
        if self.max_speed <= 0:
            self.get_logger().error(
                "Invalid max_speed parameter. It must be greater than zero. Setting to default value of 1.0."
            )
            self.max_speed = 1.0
        self.max_steering_angle = (
            self.get_parameter("max_steering_angle").get_parameter_value().double_value
        )
        self.steering_angle_offset = (
            self.get_parameter("steering_angle_offset")
            .get_parameter_value()
            .double_value
        )
        self.motor_0_pwm_pin = (
            self.get_parameter("motor_0_pwm_pin").get_parameter_value().integer_value
        )
        self.motor_0_dir_pin = (
            self.get_parameter("motor_0_dir_pin").get_parameter_value().integer_value
        )
        self.motor_1_pwm_pin = (
            self.get_parameter("motor_1_pwm_pin").get_parameter_value().integer_value
        )
        self.motor_1_dir_pin = (
            self.get_parameter("motor_1_dir_pin").get_parameter_value().integer_value
        )
        self.servo_pwm_pin = (
            self.get_parameter("servo_pwm_pin").get_parameter_value().integer_value
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
            self.m0 = DirectI2CMotor(
                self.motor_0_pwm_pin,
                self.motor_0_dir_pin,
                is_reversed=True,
                logger=self.get_logger(),
            )
            self.m1 = DirectI2CMotor(
                self.motor_1_pwm_pin,
                self.motor_1_dir_pin,
                is_reversed=False,
                logger=self.get_logger(),
            )
            self.s0 = DirectI2CServo(self.servo_pwm_pin, logger=self.get_logger())

            self.m0.speed(0.0)
            self.m1.speed(0.0)

            self.s0.angle(self.steering_angle_offset)

            self.get_logger().info("Hardware initialized successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize hardware: {e}")
            self.stop_motors()
            self.destroy_node()
            raise

    def publish_joint_state_from_msg(self, msg):
        """
        Publish a JointState message with the same names, positions, velocities, and efforts as received.
        """
        joint_state_msg = JointState()
        joint_state_msg.header.stamp = self.get_clock().now().to_msg()
        #joint_state_msg.header.frame_id = self.frame_id  # Use configurable frame_id
        joint_state_msg.name = list(msg.name)
        joint_state_msg.position = list(msg.position)
        joint_state_msg.velocity = list(msg.velocity)
        self.get_logger().debug(f"Publishing joint state: {joint_state_msg}")
        self.joint_state_pub.publish(joint_state_msg)

    def joint_command_callback(self, msg):
        """
        Callback for joint commands from topic_based_ros2_control.

        Assumes:
        - position[0]: left steering joint (radians)
        - position[1]: right steering joint (radians)
        - velocity[0]: left rear axle (m/s)
        - velocity[1]: right rear axle (m/s)

        If only one position or velocity is present, uses that value for both sides.
        """
        self.get_logger().debug(f"Received joint command: {msg}")
        with self.lock:
            # Update steering angle if present
            if msg.position and len(msg.position) > 0:
                if len(msg.position) >= 2:
                    steering_angle = (msg.position[0] + msg.position[1]) / 2.0
                else:
                    steering_angle = msg.position[0]
                self.last_steering_angle = steering_angle

            # Update speeds if present
            if msg.velocity and len(msg.velocity) > 0:
                if len(msg.velocity) >= 2:
                    left_speed = msg.velocity[0]
                    right_speed = msg.velocity[1]
                else:
                    left_speed = right_speed = msg.velocity[0]
                self.last_left_speed = left_speed
                self.last_right_speed = right_speed
            self.get_logger().debug(f"Updated speeds: left={self.last_left_speed}, right={self.last_right_speed}")   

            # Convert steering angle from radians to degrees for hardware servo
            steering_angle_deg = self.convert_radians_to_degrees(
                self.last_steering_angle
            )
            self.get_logger().debug(
                f"Left speed: {self.last_left_speed:.5f}, Right speed: {self.last_right_speed:.5f}"
            )
            # Convert wheel speeds from meters/sec to normalized value [-100, 100]
            hw_left_speed = self.to_normalized_speed(self.last_left_speed)
            hw_right_speed = self.to_normalized_speed(self.last_right_speed)
            self.get_logger().debug(
                f"Normalized: Left speed: {hw_left_speed:.5f}, Right speed: {hw_right_speed:.5f}"
            )

            # Clamp steering angle to safe range
            hw_steering_angle = max(
                -self.max_steering_angle,
                min(self.max_steering_angle, steering_angle_deg),
            )

            self.get_logger().debug(
                f"Joint Command: Steering angle (rad): {self.last_steering_angle:.2f}, (deg): {steering_angle_deg:.2f}, Clamped: {hw_steering_angle:.2f}, Left speed: {hw_left_speed:.2f}, Right speed: {hw_right_speed:.2f}"
            )

            # Apply to hardware
            self.s0.angle(
                -(hw_steering_angle + self.steering_angle_offset)
            )  # Apply steering
            self.m0.speed(hw_left_speed)  # Apply left motor speed
            self.m1.speed(hw_right_speed)  # Apply right motor speed
            self.current_speed = (hw_left_speed + hw_right_speed) / 2.0
            self.current_angle = hw_steering_angle

        self.publish_joint_state_from_msg(msg)

    def convert_radians_to_degrees(self, radians):
        """
        Converts an angle from radians to degrees.

        Args:
            radians (float): Angle in radians.

        Returns:
            float: Angle in degrees.
        """
        return math.degrees(radians)

    def to_normalized_speed(self, m_per_sec):
        """
        Converts wheel speeds from meters/sec to a normalized value in the range [-100, 100].

        Args:
            m_per_sec (float): Speed in meters per second.

        Returns:
            float: Normalized speed in the range [-100, 100].
        """
        # Ensure floating point division and no accidental integer conversion
        try:
            mps = float(m_per_sec)
            max_spd = float(self.max_speed)
        except Exception as e:
            self.get_logger().warn(f"to_normalized_speed: input conversion error: {e}")
            return 0.0
        if max_spd == 0.0:
            self.get_logger().warn("to_normalized_speed: max_speed is zero, cannot normalize.")
            return 0.0
        normalized = (mps / max_spd) * 100.0
        # Clamp to [-100, 100]
        if normalized > 100.0:
            normalized = 100.0
        elif normalized < -100.0:
            normalized = -100.0
        self.get_logger().debug(f"to_normalized_speed: m_per_sec={mps}, max_speed={max_spd}, normalized={normalized}")
        return normalized

    def stop_motors(self):
        """
        Stops the motors and resets the servo.

        This method is called during shutdown to ensure that the robot stops
        moving and the servo is reset to its default position.
        """
        self.get_logger().info("Stopping motors and resetting servo.")
        with self.lock:
            self.m0.speed(0)
            self.m1.speed(0)
            self.s0.angle(self.steering_angle_offset)

    def destroy_node(self): 
        """
        Cleans up resources before shutting down the node.

        This method stops the motors and resets the servo before calling the
        parent class's destroy_node method.
        """
        self.get_logger().info("Shutting down Picarx hardware Node.")
        self.stop_motors()
        super().destroy_node()


def main(args=None):
    """
    Main entry point for the Picarx hardware node.

    Initializes the ROS 2 node, spins it to process incoming messages, and
    ensures proper cleanup during shutdown.
    """
    rclpy.init(args=args)
    node = None
    try:
        node = PicarxHardware()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info("Node interrupted by user. Shutting down...")
    except Exception as e:
        if node:
            node.get_logger().error(f"Unhandled exception: {e}")
        raise
    finally:
        if node:
            node.stop_motors()
            node.destroy_node()
        rclpy.shutdown()


# This block ensures that the main function is executed only when the script is run directly.
if __name__ == "__main__":
    main()
