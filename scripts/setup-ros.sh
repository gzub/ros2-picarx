#!/bin/bash

# Exit on error and treat unset variables as errors
set -euo pipefail

# Default ROS distribution
ROS_DISTRO="jazzy"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ros-distro)
            ROS_DISTRO="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--ros-distro <distro>]"
            exit 1
            ;;
    esac
done

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &>/dev/null; then
        echo "Error: $1 is not installed. Please install it and try again."
        exit 1
    fi
}

# Check for required tools
check_command git
check_command vcs
check_command colcon
check_command rosdep

# Install required dependencies
echo "Installing dependencies..."
sudo apt update
sudo apt install -y git colcon python3-rosdep2 vcstool wget \
    python3-flake8-docstrings python3-pip python3-pytest-cov \
    python3-flake8-blind-except python3-flake8-builtins \
    python3-flake8-class-newline python3-flake8-comprehensions \
    python3-flake8-deprecated python3-flake8-import-order \
    python3-flake8-quotes python3-pytest-repeat python3-pytest-rerunfailures \
    python3-vcstools libx11-dev libxrandr-dev libasio-dev libtinyxml2-dev

# Create workspace directory
WORKSPACE_DIR=~/ros2_${ROS_DISTRO}
mkdir -p "${WORKSPACE_DIR}/src"

# Clone ROS2 repositories
cd "${WORKSPACE_DIR}"
echo "Importing ROS2 repositories..."
vcs import --input "https://raw.githubusercontent.com/ros2/ros2/${ROS_DISTRO}/ros2.repos" src

# Configure rosdep
echo "Configuring rosdep..."
if [ -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    sudo rm /etc/ros/rosdep/sources.list.d/20-default.list
fi
sudo rosdep init || echo "rosdep already initialized"
rosdep update

# Install dependencies
echo "Installing ROS2 dependencies..."
rosdep install --from-paths src --ignore-src --rosdistro "${ROS_DISTRO}" -y \
    --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers python3-vcstool"

# Build the workspace
echo "Building the workspace..."
colcon build --symlink-install

echo "ROS2 setup completed successfully!"