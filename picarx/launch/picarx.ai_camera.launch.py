"""
Launch file for the Raspberry Pi AI Camera Node for SunFounder PiCarX.

This launch file starts the object detection node from the raspberrypi_ai_camera_ros2
package with parameters suitable for the PiCarX robot and the IMX500-based AI camera.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Generate the launch description for the Raspberry Pi AI Camera Node.

    Launches the object_detection_node with the specified parameters for
    neural network, labels, thresholds, and output configuration.

    Returns:
        LaunchDescription: The launch description object for ROS 2 launch system.
    """
    return LaunchDescription(
        [
            Node(
                package="raspberrypi_ai_camera_ros2",
                executable="object_detection_node",
                name="picarx_rpiai_camera_node",
                output="both",
                parameters=[
                    {
                        "network_package": "/home/gzub/ros2-picarx/src/raspberrypi_ai_camera_ros2/networks/imx500_network_yolov8n_640x640_pp.rpk",
                        "labels_file": "/home/gzub/ros2-picarx/src/raspberrypi_ai_camera_ros2/labels/coco_yolo.txt",
                        "frame_id": "camera_frame",
                        "detection_threshold": 0.60,
                        "iou_threshold": 0.70,
                        "max_detections": 15,
                        "ignore_dash_labels": False,
                        "preserve_aspect_ratio": True,
                        "inference_rate": 25,
                        "output_directory": "image_out/",
                        "save_images": False,
                    }
                ],
                remappings=[
                    # Add topic remappings here if needed, e.g., ('/old_topic', '/new_topic')
                ],
            )
        ]
    )
