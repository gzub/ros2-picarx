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

# Function to clone a repository if it doesn't already exist
clone_repo() {
    local repo_url=$1
    local branch=$2
    local target_dir=$3

    if [ -d "${WORKSPACE_DIR}/${target_dir}" ]; then
        echo "${target_dir} already exists in the workspace. Skipping clone."
    else
        git clone -b "${branch}" "${repo_url}" "${WORKSPACE_DIR}/${target_dir}"
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
sudo apt install -y \
    ament-cmake-core \
    colcon \
    git \
    imx500-all \
    imx500-tools \
    libasio-dev \
    libboost1.74-all-dev \
    libmessage-filters-dev \
    libtinyxml2-dev \
    libx11-dev \
    libxrandr-dev \
    pigpio \
    pigpio-tools \
    pigpiod \
    python3-flake8-blind-except \
    python3-flake8-builtins \
    python3-flake8-class-newline \
    python3-flake8-comprehensions \
    python3-flake8-deprecated \
    python3-flake8-docstrings \
    python3-flake8-import-order \
    python3-flake8-quotes \
    python3-munkres \
    python3-opencv \
    python3-pigpio \
    python3-pip \
    python3-pytest \
    python3-pytest-cov \
    python3-pytest-repeat \
    python3-pytest-rerunfailures \
    python3-rosdep2 \
    python3-vcstools \
    software-properties-common \
    vcstool \
    wget

# Create workspace directory
WORKSPACE_DIR=$(pwd)
mkdir -p "${WORKSPACE_DIR}/src"
#check if picamera2 already exists
if [ -d "${WORKSPACE_DIR}/picamera2" ]; then
    echo "picamera2 already exists in the workspace. Skipping clone."
else
    git clone -b next https://github.com/raspberrypi/picamera2
    cd picamera2
    pip install -e . --break-system-packages
fi

# Clone ROS2 repositories
cd "${WORKSPACE_DIR}"
echo "Importing ROS2 repositories..."
echo "Using ROS2 distribution: ${ROS_DISTRO}"
echo "Importing repositories"
vcs import --input "https://raw.githubusercontent.com/ros2/ros2/${ROS_DISTRO}/ros2.repos" src

# Configure rosdep
echo "Configuring rosdep..."
# sudo rm -f /etc/ros/rosdep/sources.list.d/20-default.list
sudo rosdep init || true
rosdep update

# Install dependencies
echo "Installing ROS2 dependencies..."
rosdep install -r --from-paths src --ignore-src --rosdistro "${ROS_DISTRO}" -y \
    --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers python3-vcstool" || true

# Build the workspace
echo "Building the workspace..."
colcon build --symlink-install --packages-skip-build-finished --continue-on-error --packages-ignore  gz_ros2_control gz_ros2_control_demos gz_ros_control_tests


echo "Importing ros-controls repositories"
vcs import --input "https://raw.githubusercontent.com/ros-controls/ros2_control_ci/master/ros_controls.$ROS_DISTRO.repos" src

# Clone repositories
clone_repo https://github.com/ros-drivers/ackermann_msgs.git ros2 src/ackermann_msgs
clone_repo https://github.com/pal-robotics/backward_ros.git main src/backward_ros
clone_repo https://github.com/pal-robotics/pal_statistics.git main src/pal_statistics
clone_repo https://github.com/PickNikRobotics/generate_parameter_library.git main src/generate_parameter_library
clone_repo https://github.com/PickNikRobotics/cpp_polyfills.git main src/cpp_polyfills

# Raspberry Pi AI Camera ROS2 packages
clone_repo https://github.com/mzahana/raspberrypi_ai_camera_ros2.git main src/raspberrypi_ai_camera_ros2
clone_repo https://github.com/ros-perception/vision_opencv.git rolling src/vision_opencv
clone_repo https://github.com/Kukanani/vision_msgs.git ros2 src/vision_msgs

# Joystick ROS2 packages
clone_repo https://github.com/ros-drivers/joystick_drivers.git ros2 src/joystick_drivers

#clone_repo https://github.com/gazebo-release/gz_transport_vendor.git rolling src/gz_transport_vendor
#clone_repo https://github.com/gazebo-release/gz_msgs_vendor.git rolling src/gz_msgs_vendor
#clone_repo https://github.com/gazebosim/gz-cmake.git gz-cmake4 src/gz-cmake4
#clone_repo https://github.com/gazebosim/ros_gz.git jazzy src/ros_gz
#vcs import --input "https://raw.githubusercontent.com/gazebo-tooling/gazebodistro/master/collection-harmonic.yaml" src

# Install dependencies
echo "Installing ROS2 dependencies..."
rosdep install -r --from-paths src --ignore-src --rosdistro "${ROS_DISTRO}" -y \
    --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers python3-vcstool" || true

# Build the workspace
echo "Building the workspace..."
colcon build --symlink-install --packages-skip-build-finished --continue-on-error --packages-ignore  gz_ros2_control gz_ros2_control_demos gz_ros_control_tests

echo "ROS2 setup completed successfully!"
