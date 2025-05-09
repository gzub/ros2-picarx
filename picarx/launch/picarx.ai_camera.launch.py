from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="raspberrypi_ai_camera_ros2",
                executable="object_detection_node",
                name="picarx_rpiai_camera_node",
                output="screen",
                parameters=[
                    {
                        "network_package": "raspberrypi_ai_camera_ros2/networks/imx500_network_yolov8n_640x640_pp.rpk",
                        "labels_file": "raspberrypi_ai_camera_ros2/labels/coco_yolo.txt",
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
