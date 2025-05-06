# PicarX ROS2 Project

## Overview
This repository contains a ROS2 project for the PiCarX robot from SunFounder (see https://docs.sunfounder.com/projects/picar-x-v20/en/latest/).

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)

## Prerequisites
- A Raspberry Pi running Raspberry Pi OS.
- A user account with `sudo` permissions.
- Ensure `git` is installed: `sudo apt install git`.

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/gzub/ros2-picarx.git
   cd ros2-picarx
   ```
2. Run the script `scripts/setup-ros/sh` to automatically install and build ROS 2 on Raspberry Pi OS.  Note: This took hours to complete on a Raspberry Pi 5.

3. Install ackermann_msgs:
   ```bash
   cd ~/ros2_jazzy
   git clone -b ros2 https://github.com/ros-drivers/ackermann_msgs.git
   colcon build --packages-select ackermann_msgs
   ```

## Acknowlegements
* SunFounder robot-hat library repo is checked out into /robot_hat: https://github.com/sunfounder/robot-hat