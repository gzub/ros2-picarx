import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from rclpy.executors import SingleThreadedExecutor
import pytest

@pytest.fixture
def rclpy_init_shutdown():
    rclpy.init()
    yield
    rclpy.shutdown()

def test_picarx_node(rclpy_init_shutdown):
    from picarx.picarx import Picarx

    node = Picarx()
    executor = SingleThreadedExecutor()
    executor.add_node(node)

    # Publish a test message
    publisher = node.create_publisher(Twist, 'picarx/cmd_vel', 10)
    msg = Twist()
    msg.linear.x = 10.5
    msg.angular.z = 45.0
    publisher.publish(msg)

    # Spin the node to process the message
    executor.spin_once(timeout_sec=1.0)

    # Check the log output (or other side effects)
    # Example: Check if the status message was published
    # (This requires additional logic to capture the published message)

    node.destroy_node()