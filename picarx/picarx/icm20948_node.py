"""
ICM20948 IMU ROS 2 Node for PiCarX using SparkFun Qwiic Python library.

This node reads data from the SparkFun ICM20948 IMU via I2C and publishes:
- sensor_msgs/msg/Imu on 'imu/data'
- sensor_msgs/msg/MagneticField on 'imu/mag'
- sensor_msgs/msg/Temperature on 'imu/temperature'

Parameters:
  - frame_id (str): The frame to use in message headers (default: 'imu_link')
  - i2c_bus (int): The I2C bus number (default: 1)
  - publish_rate (float): The rate (Hz) to publish IMU data (default: 1.0)
"""

import math
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu, MagneticField, Temperature
from std_msgs.msg import Header

try:
    import qwiic_icm20948
except ImportError:
    qwiic_icm20948 = None


class ICM20948Node(Node):
    """
    ROS 2 node for SparkFun ICM20948 IMU.

    Reads IMU, magnetometer, and temperature data from the ICM20948 sensor
    and publishes them as standard ROS 2 messages.

    Covariance arrays for orientation, angular velocity, and linear acceleration
    are set to `-1.0` to indicate unknown values, following ROS conventions.
    """

    def __init__(self):
        """
        Initialize the ICM20948Node.

        Sets up publishers for IMU, magnetometer, and temperature data.
        Initializes the ICM20948 sensor and starts a timer for periodic publishing.
        """
        super().__init__("icm20948_node")

        self.declare_parameter("frame_id", "imu_link")
        self.declare_parameter("i2c_bus", 1)
        self.declare_parameter("frequency", 15.0)  # Default to 15Hz for IMU

        # Use get_parameter_value().string_value for frame_id to ensure correct type for ROS Header
        self.frame_id = (
            self.get_parameter("frame_id").get_parameter_value().string_value
        )
        self.i2c_bus = self.get_parameter("i2c_bus").get_parameter_value().integer_value
        self.frequency = (
            self.get_parameter("frequency").get_parameter_value().double_value
        )
        if self.frequency <= 0.0:
            self.get_logger().warn("frequency must be > 0. Using 15.0 Hz.")
            self.frequency = 15.0

        if qwiic_icm20948 is None:
            self.get_logger().error(
                "qwiic_icm20948 library not found. Please install it."
            )
            raise ImportError("qwiic_icm20948 not installed")

        self.imu = qwiic_icm20948.QwiicIcm20948()
        if hasattr(self.imu, "useBus"):
            self.imu.useBus(self.i2c_bus)
        if not self.imu.connected:
            self.get_logger().error(
                f"ICM20948 IMU not detected on I2C bus {self.i2c_bus}"
            )
            self.get_logger().error("Shutting down node due to IMU connection failure.")
            # Don't call destroy_node() before node is fully constructed
            rclpy.shutdown()
            return
        begin_result = self.imu.begin()
        # If begin() returns a status, check for failure (SparkFun returns True on success)
        if begin_result is not None and begin_result is not True:
            self.get_logger().error("ICM20948 IMU initialization failed.")
            rclpy.shutdown()
            return
        self.get_logger().info("ICM20948 IMU initialized.")

        self.imu_publisher = self.create_publisher(
            Imu, "imu/data_raw", qos_profile_sensor_data
        )
        self.mag_publisher = self.create_publisher(
            MagneticField, "imu/mag", qos_profile_sensor_data
        )
        self.temp_publisher = self.create_publisher(
            Temperature, "imu/temperature", qos_profile_sensor_data
        )

        timer_period = 1.0 / self.frequency
        self.timer = self.create_timer(timer_period, self.publish_imu)
        self.lock = threading.Lock()

    def publish_imu(self):
        """
        Read IMU, magnetometer, and temperature data from the sensor and publish as ROS 2 messages.
        """
        with self.lock:
            if not self.imu.dataReady():
                self.get_logger().debug("IMU data not ready.")
                return
            self.imu.getAgmt()  # Updates all sensor values

            # sensor_msgs/msg/Imu message
            imu_msg = Imu()
            imu_msg.header = Header()
            imu_msg.header.stamp = self.get_clock().now().to_msg()
            imu_msg.header.frame_id = self.frame_id

            # Orientation (not provided, set to identity quaternion, unknown covariance)
            imu_msg.orientation.x = 0.0
            imu_msg.orientation.y = 0.0
            imu_msg.orientation.z = 0.0
            imu_msg.orientation.w = 0.0
            imu_msg.orientation_covariance = [-1.0] * 9  # -1: orientation not provided

            # Angular velocity (rad/s, REP-103: invert Z)
            gx_dps = self.imu.gxRaw / 131.0
            gy_dps = self.imu.gyRaw / 131.0
            gz_dps = self.imu.gzRaw / 131.0
            imu_msg.angular_velocity.x = float(gx_dps * (math.pi / 180.0))
            imu_msg.angular_velocity.y = float(gy_dps * (math.pi / 180.0))
            imu_msg.angular_velocity.z = float(-gz_dps * (math.pi / 180.0))

            # Linear acceleration (m/s^2, REP-103: invert Z, remove gravity)
            ax = (self.imu.axRaw / 16384.0) * 9.80665
            ay = (self.imu.ayRaw / 16384.0) * 9.80665
            az = -((self.imu.azRaw / 16384.0) * 9.80665) + 9.80665
            imu_msg.linear_acceleration.x = float(ax)
            imu_msg.linear_acceleration.y = float(ay)
            imu_msg.linear_acceleration.z = float(az)

            self.imu_publisher.publish(imu_msg)
            # Use debug for high-frequency topics
            self.get_logger().debug(
                f"Published IMU: accel=({imu_msg.linear_acceleration.x:.2f}, {imu_msg.linear_acceleration.y:.2f}, {imu_msg.linear_acceleration.z:.2f}) "
                f"gyro=({imu_msg.angular_velocity.x:.2f}, {imu_msg.angular_velocity.y:.2f}, {imu_msg.angular_velocity.z:.2f})"
            )

            # Magnetometer message
            mag_msg = MagneticField()
            mag_msg.header = imu_msg.header
            # μT to Tesla (SI): multiply by 1e-6, invert Z for REP-103
            mag_msg.magnetic_field.x = self.imu.mxRaw * 0.15 * 1e-6
            mag_msg.magnetic_field.y = self.imu.myRaw * 0.15 * 1e-6
            mag_msg.magnetic_field.z = -self.imu.mzRaw * 0.15 * 1e-6
            self.mag_publisher.publish(mag_msg)
            self.get_logger().debug(
                f"Published Mag: mag=({mag_msg.magnetic_field.x:.2e}, {mag_msg.magnetic_field.y:.2e}, {mag_msg.magnetic_field.z:.2e})"
            )

            # Temperature message
            temp_msg = Temperature()
            temp_msg.header = imu_msg.header
            try:
                temp_msg.temperature = float(self.imu.tmpRaw) / 100.0
            except Exception as e:
                self.get_logger().error(
                    f"Failed to convert temperature: {self.imu.tmpRaw} to float: {e}"
                )
                temp_msg.temperature = float("nan")
            temp_msg.variance = 0.5  # Example: set a reasonable variance
            self.temp_publisher.publish(temp_msg)
            self.get_logger().debug(f"Published Temp: {temp_msg.temperature:.2f} C")


def main(args=None):
    """
    Main entry point for the ICM20948Node.

    Initializes the ROS 2 node, spins it to process incoming messages, and
    ensures proper cleanup during shutdown.
    """
    rclpy.init(args=args)
    node = None
    rclpy.logging.get_logger("ICM20948Node").info("Starting ICM20948Node...")
    try:
        node = ICM20948Node()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()
