#!/bin/bash

###############################################################################
# setup-ros.sh
#
# This script automates the setup of a ROS 2 workspace for the PiCarX project.
# It installs required dependencies, clones and updates necessary repositories,
# configures rosdep, and builds the workspace using colcon.
#
# Usage:
#   ./scripts/setup-ros.sh [--ros-distro <distro>] [--no-skip-build-finished]
#
# Options:
#   --ros-distro <distro>           Specify the ROS 2 distribution (default: kilted)
#   --no-skip-build-finished        Do not use --packages-skip-build-finished for colcon build
#
# The script is idempotent and can be run multiple times to update sources.
#
# Key Features:
#   - Installs system and Python dependencies
#   - Clones and updates all required ROS 2 and third-party repositories
#   - Handles missing binary packages by skipping them in rosdep
#   - Applies workaround for Fast-DDS build issues with GCC 12+
#   - Builds the workspace with colcon
#
# NOTE: This script is intended for Raspberry Pi OS (tested on Pi 5, Bookworm).
###############################################################################

# Exit on error and treat unset variables as errors
set -euo pipefail

# Default ROS distribution and build options
ROS_DISTRO="kilted"
SKIP_BUILD_FINISHED=1

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
    --ros-distro)
        ROS_DISTRO="$2"
        shift 2
        ;;
    --no-skip-build-finished)
        SKIP_BUILD_FINISHED=0
        shift
        ;;
    *)
        echo "Unknown option: $1"
        echo "Usage: $0 [--ros-distro <distro>] [--no-skip-build-finished]"
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
        echo "${target_dir} already exists in the workspace. Updating..."
        pushd "${WORKSPACE_DIR}/${target_dir}" >/dev/null
        git fetch --all
        # Warn if there are local changes
        if ! git diff-index --quiet HEAD --; then
            echo "Warning: Local changes detected in ${target_dir}."
        fi
        git checkout -B "${branch}" "origin/${branch}"
        git pull

        popd >/dev/null
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
    python3-transforms3d \
    python3-vcstools \
    software-properties-common \
    vcstool \
    wget

# Create workspace directory
WORKSPACE_DIR=$(pwd)
mkdir -p "${WORKSPACE_DIR}/src"

# Install picamera2 if not already installed
if [ ! -d "${WORKSPACE_DIR}/picamera2" ]; then
    clone_repo https://github.com/raspberrypi/picamera2.git next picamera2
else
    echo "picamera2 already exists in the workspace. Updating..."
    pushd picamera2 >/dev/null
    git fetch origin
    git checkout next
    git pull
    popd >/dev/null
fi
pip install -e "${WORKSPACE_DIR}/picamera2" --break-system-packages

sudo pip install --break-system-packages sparkfun-qwiic-icm20948

# Clone ROS2 repositories
cd "${WORKSPACE_DIR}"
echo "Importing ROS2 repositories..."
echo "Using ROS2 distribution: ${ROS_DISTRO}"
echo "Importing repositories"
vcs import --input "https://raw.githubusercontent.com/ros2/ros2/${ROS_DISTRO}/ros2.repos" src

# Configure rosdep
echo "Configuring rosdep..."
sudo rosdep init || true
rosdep update

echo "Importing ros-controls repositories"
vcs import --input "https://raw.githubusercontent.com/ros-controls/ros2_control_ci/master/ros_controls.$ROS_DISTRO.repos" src

# Clone repositories
clone_repo https://github.com/ros-drivers/ackermann_msgs.git ros2 src/ackermann_msgs
clone_repo https://github.com/pal-robotics/backward_ros.git foxy-devel src/backward_ros
clone_repo https://github.com/pal-robotics/pal_statistics.git humble-devel src/pal_statistics
clone_repo https://github.com/PickNikRobotics/generate_parameter_library.git main src/generate_parameter_library
clone_repo https://github.com/PickNikRobotics/cpp_polyfills.git main src/cpp_polyfills

# Raspberry Pi AI Camera ROS2 packages
#clone_repo https://github.com/mzahana/raspberrypi_ai_camera_ros2.git camerainfo src/raspberrypi_ai_camera_ros2
clone_repo https://github.com/gzub/raspberrypi_ai_camera_ros2.git main raspberrypi_ai_camera_ros2
clone_repo https://github.com/ros-perception/vision_opencv.git rolling src/vision_opencv
clone_repo https://github.com/Kukanani/vision_msgs.git ros2 src/vision_msgs

# Joystick ROS2 packages
echo Installing Joystick
clone_repo https://github.com/ros-drivers/joystick_drivers.git ros2 src/joystick_drivers

# Web video server ROS2 packages
echo Installing Web Video Server
clone_repo https://github.com/fkie/async_web_server_cpp.git "ros2-develop" src/async_web_server_cpp
clone_repo https://github.com/RobotWebTools/web_video_server.git ros2 src/web_video_server

# Topic Based ROS2 Control
echo Installing Topic Based Control
clone_repo https://github.com/gzub/topic_based_ros2_control.git main topic_based_ros2_control

# Nav2
echo Installing Navigation2
clone_repo https://github.com/ros-navigation/navigation2.git ${ROS_DISTRO} ./src/navigation2
clone_repo https://github.com/DLu/tf_transformations.git main ./src/tf_transformations
clone_repo https://github.com/ros-geographic-info/geographic_info.git ros2 ./src/geographic_info
clone_repo https://github.com/SteveMacenski/slam_toolbox.git ${ROS_DISTRO} ./src/slam_toolbox
clone_repo https://github.com/cra-ros-pkg/robot_localization.git ros2 ./src/robot_localization
clone_repo https://github.com/BehaviorTree/BehaviorTree.CPP.git master ./src/BehaviorTree.CPP
clone_repo https://github.com/ros/bond_core.git ros2 ./src/bond_core

# IMUTools
# echo Installing IMUTools
# clone_repo https://github.com/CCNYRoboticsLab/imu_tools.git ${ROS_DISTRO} src/imu_tools
# clone_repo https://github.com/ros-perception/imu_pipeline.git ros2 src/imu_pipeline

# rqt_tf_tree
echo Installing rqt_tf_tree
clone_repo https://github.com/ros-visualization/rqt_tf_tree.git humble src/rqt_tf_tree

# Install dependencies
echo "Installing ROS2 dependencies..."
rosdep install -r --from-paths src --ignore-src --rosdistro "${ROS_DISTRO}" -y \
    --skip-keys "nav2_system_tests fastcdr rti-connext-dds-6.0.1 urdfdom_headers python3-vcstool ros-${ROS_DISTRO}-ros-gz-bridge ros-${ROS_DISTRO}-ros-gz-sim rti-connext-dds-7.3.0-ros ros-${ROS_DISTRO}-gz-sim-vendor ros-${ROS_DISTRO}-gz-plugin-vendor ros-${ROS_DISTRO}-ackermann-msgs ros-${ROS_DISTRO}-sdformat-urdf" || true

# Build the workspace (second build)
echo "Building the workspace..."
export CMAKE_CXX_FLAGS="-Wno-error=maybe-uninitialized"

COLCON_ARGS=(
    --symlink-install
    --continue-on-error
    --packages-ignore nav2_system_tests gz_ros2_control gz_ros2_control_demos rosbag2_examples_cpp rosbag2_tests rosbag2_tests test_tracetools
    --cmake-args -DCMAKE_CXX_FLAGS="-Wno-error=maybe-uninitialized"
)
if [ "$SKIP_BUILD_FINISHED" -eq 1 ]; then
    COLCON_ARGS+=(--packages-skip-build-finished)
fi

colcon build "${COLCON_ARGS[@]}"

echo "ROS2 setup completed successfully!"
