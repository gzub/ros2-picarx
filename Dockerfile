FROM ros:jazzy-ros-base

# Install necessary tools
RUN apt-get update && apt-get install -y python3-pip

# Create a workspace directory
WORKDIR /app

# Copy your ROS 2 package into the container
COPY ./my_python_pkg /app/my_python_pkg
# Install Python dependencies (if any)
# RUN python3 -m pip install -r /app/my_car_controller/requirements.txt

# Build the ROS 2 package
WORKDIR /app
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --packages-select my_python_pkg

# Source the ROS 2 environment and run your node
CMD ["bash", "-c", ". /opt/ros/jazzy/setup.sh && ros2 run my_python_pkg car_control_node"]