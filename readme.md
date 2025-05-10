# PicarX ROS2 Project

## Overview
This repository contains a ROS2 project for the PiCarX robot from SunFounder (see https://docs.sunfounder.com/projects/picar-x-v20/en/latest/).  I swapped the camera for the Raspberry Pi AI camera.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)

## Prerequisites
- A Raspberry Pi running Raspberry Pi OS (this was done on a Raspberry Pi 5 with bookworm).
- A user account with `sudo` permissions.
- Ensure `git` is installed: `sudo apt install git`.

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/gzub/ros2-picarx.git
   cd ros2-picarx
   ```
2. Run the script `scripts/setup-ros/sh` to automatically install and build ROS 2 on Raspberry Pi OS.  Note: This took hours to complete on a Raspberry Pi 5.
3. Install libboost 1.74:
   ```bash
   sudo apt-get install libboost1.74-all-dev.
   ```
git clone https://github.com/ros-controls/ros2_control.git
git clone https://github.com/ros-controls/ros2_controllers.git
git clone https://github.com/ros-controls/control_msgs.gitcolcon 
git clone https://github.com/pal-robotics/backward_ros
git clone https://github.com/ros-controls/ros2_control_cmake.git
git clone https://github.com/PickNikRobotics/RSL.git
git clone https://github.com/PickNikRobotics/generate_parameter_library.git
git clone https://github.com/PickNikRobotics/cpp_polyfills.git
git clone https://github.com/ros-controls/realtime_tools.git
git clone https://github.com/pal-robotics/pal_statistics.git

 git clone https://github.com/ros/diagnostics.git
 build --packages-above-and-dependencies ros2_control ros2_controllers

## Sample command lines
### raspberrypi_ai_camera_ros2
```bash
ros2 run raspberrypi_ai_camera_ros2 object_detection_node --ros-args \
    -p network_package:="install/raspberrypi_ai_camera_ros2/share/raspberrypi_ai_camera_ros2/networks/imx500_network_yolov8n_640x640_pp.rpk" \
    -p labels_file:="install/raspberrypi_ai_camera_ros2/share/raspberrypi_ai_camera_ros2/labels/coco_yolo.txt" \
    -p frame_id:="camera_frame" \
    -p detection_threshold:=0.60 \
    -p iou_threshold:=0.70 \
    -p max_detections:=15 \
    -p ignore_dash_labels:=false \
    -p preserve_aspect_ratio:=true \
    -p inference_rate:=25 \
    -p output_directory:="image_out/" \
    -p save_images:=true
```
```
ros2 topic pub picarx/cmd_ackermann ackermann_msgs/msg/AckermannDrive "{steering_angle: 30, steering_angle_velocity: 0.2, speed: 0}
```
## Acknowlegements
* SunFounder robot-hat library repo is checked out into /robot_hat: https://github.com/sunfounder/robot-hat