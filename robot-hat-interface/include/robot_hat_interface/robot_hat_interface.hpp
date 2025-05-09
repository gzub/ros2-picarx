#ifndef ROBOT_HAT_INTERFACE__ROBOT_HAT_INTERFACE_HPP_
#define ROBOT_HAT_INTERFACE__ROBOT_HAT_INTERFACE_HPP_

#include <hardware_interface/system_interface.hpp>
#include <rclcpp_lifecycle/state.hpp>
#include <vector>
#include <string>

namespace robot_hat_interface
{
class RobotHatHardware : public hardware_interface::SystemInterface
{
public:
  hardware_interface::CallbackReturn on_configure(const rclcpp_lifecycle::State & previous_state) override;
  hardware_interface::CallbackReturn on_activate(const rclcpp_lifecycle::State & previous_state) override;
  hardware_interface::CallbackReturn on_deactivate(const rclcpp_lifecycle::State & previous_state) override;
  hardware_interface::CallbackReturn on_cleanup(const rclcpp_lifecycle::State & previous_state) override;

  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  hardware_interface::return_type read(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;
  hardware_interface::return_type write(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  // Joint names
  std::string left_wheel_name_;
  std::string right_wheel_name_;
  std::string steering_servo_name_;

  // State variables
  double left_wheel_state_pos_{0.0};
  double left_wheel_state_vel_{0.0};
  double right_wheel_state_pos_{0.0};
  double right_wheel_state_vel_{0.0};
  double steering_servo_state_pos_{0.0};
  double steering_servo_state_vel_{0.0};

  // Command variables
  double left_wheel_command_{0.0};
  double right_wheel_command_{0.0};
  double steering_servo_command_{0.0};

  // GPIO-related variables (e.g., pigpio handles)
  int left_motor_pwm_pin_;
  int left_motor_dir_pin_;
  int right_motor_pwm_pin_;
  int right_motor_dir_pin_;
  int steering_servo_pin_;

  int lgpio_handle;  // Handle for the GPIO chip
};
}  // namespace robot_hat_interface

#endif  // ROBOT_HAT_INTERFACE__ROBOT_HAT_INTERFACE_HPP_
