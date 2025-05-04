# Sample ROS 2 node
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from ackermann_msgs.msg import AckermannDrive  # Assuming standard Ackermann topic
from sensor_msgs.msg import Range

class ObstacleAvoidanceNode(Node):

    def __init__(self):
        super().__init__("obstacle_avoidance")

        # Define QoS profile
        qos_profile = QoSProfile(depth=10)

        # Subscribe to ultrasonic sensor
        self.subscription = self.create_subscription(
            Range,
            "picarx/ultrasonic_sensor",
            self.sensor_callback,
            qos_profile
        )

        # Publish to cmd_ackermann
        self.publisher_ = self.create_publisher(AckermannDrive, "picarx/cmd_ackermann", qos_profile)

        # Define minimum distance parameter
        self.declare_parameter("min_distance", 0.5)  # meters
        self.min_distance = self.get_parameter("min_distance").value

    def sensor_callback(self, msg):
        """
        Callback function for the ultrasonic sensor topic.
        """
        try:
            self.get_logger().info("Received range: %.2f meters" % msg.range)
            if msg.range < 0.0:
                self.get_logger().warn("Received invalid range value: %f" % msg.range)
                return

            if msg.range <= self.min_distance:  # Check if object is close
                self.get_logger().info("Object detected within %.2f meters (%.2f meters). Stopping!" % (self.min_distance, msg.range))
                # Publish stop command
                stop_command = AckermannDrive()
                stop_command.speed = 0.0  # Stop the vehicle
                stop_command.steering_angle = 0.0  # Stop steering

                self.publisher_.publish(stop_command)
            else:
                self.get_logger().info("Object is %.2f meters away. Continuing." % msg.range)

        except Exception as e:
            self.get_logger().error("Error in sensor callback: %s" % str(e))


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidanceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()