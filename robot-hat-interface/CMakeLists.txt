cmake_minimum_required(VERSION 3.8)
project(robot_hat_interface)

if(CMAKE_COMPILER_ID STREQUAL "GNU" OR CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Include common dependencies declared visible in the package.xml
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(ros2_control REQUIRED)
find_package(urdf REQUIRED)
find_package(xacro REQUIRED)
find_package(PkgConfig REQUIRED)

# Add this line to include the custom Findpigpio.cmake
list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

# Remove references to pigpio and add lgpio
find_library(LGPIO_LIBRARY NAMES lgpio REQUIRED)
find_path(LGPIO_INCLUDE_DIR NAMES lgpio.h REQUIRED)

include_directories(
  include
)

# Declare a C++ library
add_library(robot_hat_interface SHARED
  src/robot_hat_interface.cpp
)

ament_target_dependencies(robot_hat_interface
  rclcpp
  rclcpp_lifecycle
  hardware_interface
  pluginlib
  ros2_control
  urdf
  xacro
)

target_include_directories(robot_hat_interface PRIVATE ${LGPIO_INCLUDE_DIR})
target_link_libraries(robot_hat_interface ${LGPIO_LIBRARY})

# Install the library, headers, and pluginlib XML file
install(TARGETS robot_hat_interface
  DESTINATION lib
)

install(
  DIRECTORY include/
  DESTINATION include
)

install(
  FILES robot_hat_interface.xml
  DESTINATION share/${PROJECT_NAME}
)

pluginlib_export_plugin_description_file(
  hardware_interface robot_hat_interface.xml)

# Install URDF and Xacro files
install(
  DIRECTORY urdf/
  DESTINATION share/${PROJECT_NAME}/urdf
  FILES_MATCHING PATTERN "*.xacro" PATTERN "*.urdf"
)

# Install configuration files
install(
  DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

# Install launch files
install(
  DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

ament_package()
