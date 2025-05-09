#include "robot_hat_interface/robot_hat_interface.hpp"
#include <lgpio.h>  // Include lgpio header
#include <rclcpp/logging.hpp>
#include "pluginlib/class_list_macros.hpp"

#include <iostream>
#include <string>
#include <limits>
#include <cmath>  // For M_PI

#include "hardware_interface/types/hardware_interface_type_values.hpp"

namespace robot_hat_interface
{
rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn RobotHatHardware::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) !=
      rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::SUCCESS)
  {
    return rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::ERROR;
  }

  if (info.joints.size() != 3) {
    RCLCPP_ERROR(rclcpp::get_logger("RobotHatHardware"), "Expected 3 joints, but got %zu", info.joints.size());
    return rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::ERROR;
  }

  // Assign joint names
  left_wheel_name_ = info.joints[0].name;
  right_wheel_name_ = info.joints[1].name;
  steering_servo_name_ = info.joints[2].name;

  // Initialize GPIO (e.g., lgpio)
  lgpio_handle = lgGpiochipOpen(0);  // Open GPIO chip 0
  if (lgpio_handle < 0) {
    RCLCPP_ERROR(rclcpp::get_logger("RobotHatHardware"), "Failed to open GPIO chip");
    return rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::ERROR;
  }

  // Set GPIO pins for motors and servo
  left_motor_pwm_pin_ = 12;  // Example GPIO pin
  left_motor_dir_pin_ = 13;
  right_motor_pwm_pin_ = 18;
  right_motor_dir_pin_ = 19;
  steering_servo_pin_ = 2;

  lgGpioClaimOutput(lgpio_handle, 0, left_motor_pwm_pin_, 0);  // Set initial level to 0
  lgGpioClaimOutput(lgpio_handle, 0, left_motor_dir_pin_, 0);
  lgGpioClaimOutput(lgpio_handle, 0, right_motor_pwm_pin_, 0);
  lgGpioClaimOutput(lgpio_handle, 0, right_motor_dir_pin_, 0);
  lgGpioClaimOutput(lgpio_handle, 0, steering_servo_pin_, 0);

  return rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RobotHatHardware::on_configure(const rclcpp_lifecycle::State &)
{
  RCLCPP_INFO(rclcpp::get_logger("RobotHatHardware"), "Configuring hardware...");
  // Add your hardware configuration logic here
  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> RobotHatHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;

  state_interfaces.emplace_back(hardware_interface::StateInterface(
    left_wheel_name_, hardware_interface::HW_IF_POSITION, &left_wheel_state_pos_));
  state_interfaces.emplace_back(hardware_interface::StateInterface(
    left_wheel_name_, hardware_interface::HW_IF_VELOCITY, &left_wheel_state_vel_));

  state_interfaces.emplace_back(hardware_interface::StateInterface(
    right_wheel_name_, hardware_interface::HW_IF_POSITION, &right_wheel_state_pos_));
  state_interfaces.emplace_back(hardware_interface::StateInterface(
    right_wheel_name_, hardware_interface::HW_IF_VELOCITY, &right_wheel_state_vel_));

  state_interfaces.emplace_back(hardware_interface::StateInterface(
    steering_servo_name_, hardware_interface::HW_IF_POSITION, &steering_servo_state_pos_));
  state_interfaces.emplace_back(hardware_interface::StateInterface(
    steering_servo_name_, hardware_interface::HW_IF_VELOCITY, &steering_servo_state_vel_));

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> RobotHatHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  command_interfaces.emplace_back(hardware_interface::CommandInterface(
    left_wheel_name_, hardware_interface::HW_IF_VELOCITY, &left_wheel_command_));
  command_interfaces.emplace_back(hardware_interface::CommandInterface(
    right_wheel_name_, hardware_interface::HW_IF_VELOCITY, &right_wheel_command_));
  command_interfaces.emplace_back(hardware_interface::CommandInterface(
    steering_servo_name_, hardware_interface::HW_IF_POSITION, &steering_servo_command_));

  return command_interfaces;
}

hardware_interface::CallbackReturn RobotHatHardware::on_activate(const rclcpp_lifecycle::State &)
{
  RCLCPP_INFO(rclcpp::get_logger("RobotHatHardware"), "Activating hardware...");
  // Add your hardware activation logic here
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RobotHatHardware::on_deactivate(const rclcpp_lifecycle::State &)
{
  RCLCPP_INFO(rclcpp::get_logger("RobotHatHardware"), "Deactivating hardware...");
  // Add your hardware deactivation logic here
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RobotHatHardware::on_cleanup(const rclcpp_lifecycle::State &)
{
  RCLCPP_INFO(rclcpp::get_logger("RobotHatHardware"), "Cleaning up hardware...");

  // Stop PWM and servo outputs by setting GPIO pins to low
  lgGpioWrite(lgpio_handle, left_motor_pwm_pin_, 0);
  lgGpioWrite(lgpio_handle, left_motor_dir_pin_, 0);
  lgGpioWrite(lgpio_handle, right_motor_pwm_pin_, 0);
  lgGpioWrite(lgpio_handle, right_motor_dir_pin_, 0);
  lgGpioWrite(lgpio_handle, steering_servo_pin_, 0);

  // Close GPIO chip
  lgGpiochipClose(lgpio_handle);

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type RobotHatHardware::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Update state variables (e.g., read encoder values)
  // Placeholder: Simulate state updates
  left_wheel_state_pos_ += left_wheel_state_vel_ * 0.1;  // Simulate position update
  right_wheel_state_pos_ += right_wheel_state_vel_ * 0.1;
  steering_servo_state_pos_ = steering_servo_command_;  // Simulate servo position

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type RobotHatHardware::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Set GPIO pins for left motor direction and PWM
  lgGpioWrite(lgpio_handle, left_motor_pwm_pin_, std::abs(left_wheel_command_) > 0 ? 1 : 0);
  lgGpioWrite(lgpio_handle, left_motor_dir_pin_, left_wheel_command_ >= 0 ? 1 : 0);

  // Set GPIO pins for right motor direction and PWM
  lgGpioWrite(lgpio_handle, right_motor_pwm_pin_, std::abs(right_wheel_command_) > 0 ? 1 : 0);
  lgGpioWrite(lgpio_handle, right_motor_dir_pin_, right_wheel_command_ >= 0 ? 1 : 0);

  // Calculate pulse width for servo (in microseconds)
  int pulse_width = static_cast<int>(1000 + (steering_servo_command_ + M_PI) * 1000 / M_PI);  // Map -π to π to 1000-2000 µs

  // Convert pulse width to duty cycle (percentage of PWM period)
  const int pwm_period = 20000;  // 50 Hz PWM signal (20 ms period)
  int duty_cycle = (pulse_width * 100) / pwm_period;  // Convert pulse width to duty cycle percentage

  // Simulate servo control by toggling GPIO pin (placeholder logic)
  lgGpioWrite(lgpio_handle, steering_servo_pin_, duty_cycle > 50 ? 1 : 0);

  return hardware_interface::return_type::OK;
}

} // namespace robot_hat_interface

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  robot_hat_interface::RobotHatHardware,
  hardware_interface::SystemInterface)
