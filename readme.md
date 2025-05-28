# PicarX ROS2 Project

## Overview
This repository contains a ROS2 project for the PiCarX robot from SunFounder (see https://docs.sunfounder.com/projects/picar-x-v20/en/latest/).  I swapped the camera for the Raspberry Pi AI camera.

## Table of Contents
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Sample command lines](#sample-command-lines)
- [Acknowledgements](#acknowledgements)

## Project Structure
The repository is organized as follows:
- `picarx/` - Custom ROS2 packages and nodes for PiCarX control, sensors, and integrations.
- `src/` - Unmodified upstream ROS2 source and third-party packages.
- `scripts/` - Utility scripts, including ROS2 setup and build scripts.
- `install/`, `build/`, `log/` - ROS2 workspace build artifacts (created after building).
- `config/` - Configuration files for nodes and launch files.

## Prerequisites
- Raspberry Pi running Raspberry Pi OS (tested on Raspberry Pi 5, Bookworm).
- User account with `sudo` permissions.
- `git` installed: `sudo apt install git`.
- Sufficient free disk space and internet connection.

## Installation
1. **Clone this repository:**
   ```bash
   git clone https://github.com/gzub/ros2-picarx.git
   cd ros2-picarx
   ```

2. **Run the setup script:**  
   The `scripts/setup-ros.sh` script will:
   - Install ROS2 and all required dependencies.
   - Clone and set up required ROS2 control packages.
   - Build the workspace using `colcon`.
   - Optionally install extra drivers and utilities.
   ```bash
   ./scripts/setup-ros.sh
   ```
   > **Note:** The script may take several hours to complete on a Raspberry Pi 5.
