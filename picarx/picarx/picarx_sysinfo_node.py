"""
Picarx System Info Node for SunFounder PiCarX (Robot Hat v4, ROS 2 Jazzy).

This node publishes Raspberry Pi system information including CPU temperature,
system load average, and battery voltage (via Robot Hat). It is designed for
use on Raspberry Pi OS (Pi 5) and is compatible with ROS 2 Jazzy.

Publishes:
- sensor_msgs/msg/Temperature (cpu_temperature)
- std_msgs/msg/Float32 (loadavg_1min, loadavg_5min, loadavg_15min)
- std_msgs/msg/Float32 (battery_voltage)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from sensor_msgs.msg import Temperature

from robot_hat.utils import get_battery_voltage


class PicarxSysInfoNode(Node):
    """
    ROS 2 node that publishes Raspberry Pi system info: CPU temperature,
    load average, and battery voltage.
    """

    def __init__(self):
        """
        Initialize the PicarxSysInfoNode.

        Sets up ROS 2 publishers for CPU temperature, load averages, and battery voltage.
        Starts a timer to periodically publish system information.
        """
        super().__init__("picarx_sysinfo_node")

        self.temp_pub = self.create_publisher(Temperature, "/cpu_temperature", 10)
        self.loadavg1_pub = self.create_publisher(Float32, "/loadavg_1min", 10)
        self.loadavg5_pub = self.create_publisher(Float32, "/loadavg_5min", 10)
        self.loadavg15_pub = self.create_publisher(Float32, "/loadavg_15min", 10)
        self.voltage_pub = self.create_publisher(Float32, "/battery_voltage", 10)

        self.timer = self.create_timer(2.0, self.timer_callback)  # 0.5 Hz

        self.get_logger().info("PicarxSysInfoNode started.")

    def timer_callback(self):
        """
        Timer callback to read and publish system information.

        Reads CPU temperature from /sys/class/thermal/thermal_zone0/temp,
        load averages from /proc/loadavg, and battery voltage using
        robot_hat.utils.get_battery_voltage(). Publishes the data to
        corresponding ROS 2 topics.
        """
        # CPU Temperature
        try:
            with open(
                "/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8"
            ) as f:
                temp_milli = int(f.read().strip())
                temp_c = temp_milli / 1000.0
            temp_msg = Temperature()
            temp_msg.temperature = temp_c
            temp_msg.variance = 0.0
            self.temp_pub.publish(temp_msg)
        except Exception as e:
            self.get_logger().warn(f"Failed to read CPU temperature: {e}")

        # Load Average
        try:
            with open("/proc/loadavg", "r", encoding="utf-8") as f:
                loadavgs = f.read().strip().split()[:3]
                load1, load5, load15 = map(float, loadavgs)
            self.loadavg1_pub.publish(Float32(data=load1))
            self.loadavg5_pub.publish(Float32(data=load5))
            self.loadavg15_pub.publish(Float32(data=load15))
        except Exception as e:
            self.get_logger().warn(f"Failed to read loadavg: {e}")

        # Battery Voltage
        try:
            voltage = get_battery_voltage()
            if voltage is not None and voltage > 0:
                self.voltage_pub.publish(Float32(data=voltage))
        except Exception as e:
            self.get_logger().warn(f"Failed to read battery voltage: {e}")


def main(args=None):
    """
    Entry point for the PicarxSysInfoNode.

    Initializes the ROS 2 Python client library, starts the node, and
    spins until shutdown.
    """
    rclpy.init(args=args)
    node = None
    try:
        node = PicarxSysInfoNode()
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
