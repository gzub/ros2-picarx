"""
hardware_interface.py
---------------------
Hardware abstraction classes for the SunFounder Robot Hat v4 board, used in the PiCarX ROS2 project.

This module provides reusable classes for I2C bus access, PWM control, direct motor control,
and direct servo control.
These classes are designed to be used by ROS2 nodes and other components that need to interact
with the Robot Hat v4 hardware.

Classes:
    - I2CBus: Abstraction for I2C bus initialization and access.
    - PWM: PWM controller for Robot Hat v4 using I2C (smbus2).
    - DirectI2CMotor: Direct I2C motor control for Robot Hat v4.
    - DirectI2CServo: Direct I2C servo control for Robot Hat v4.
"""

import logging
import time
from enum import Enum

import smbus2
from gpiozero import InputDevice, OutputDevice


class I2CBus:
    """
    Abstraction for I2C bus initialization and access using smbus2.
    Provides methods for reading, writing, scanning, and memory operations on I2C devices.
    """

    def read(self, length=1):
        """
        Read data from I2C device. Reads bytes one at a time.
        """
        if not isinstance(length, int):
            raise ValueError(f"length must be int, not {type(length)}")
        result = []
        for _ in range(length):
            result.append(self.bus.read_byte(self.i2c_addr))
        return result

    def _convert_data(self, data):
        """
        Helper to convert data to a list of bytes for I2C operations.
        """
        if isinstance(data, bytearray):
            return list(data)
        elif isinstance(data, int):
            if data == 0:
                return [0]
            else:
                data_all = []
                while data > 0:
                    data_all.append(data & 0xFF)
                    data >>= 8
                return data_all
        elif isinstance(data, list):
            return data
        else:
            raise ValueError(
                f"I2C data must be int, list, or bytearray, not {type(data)}"
            )

    def write(self, data):
        """
        Write data to the I2C device. Handles int, list, bytearray, and dispatches to the correct SMBus method.
        """
        data_all = self._convert_data(data)
        # Write data
        if len(data_all) == 1:
            self.bus.write_byte(self.i2c_addr, data_all[0])
        elif len(data_all) == 2:
            self.bus.write_byte_data(self.i2c_addr, data_all[0], data_all[1])
        elif len(data_all) == 3:
            reg = data_all[0]
            value = (data_all[2] << 8) + data_all[1]
            self.bus.write_word_data(self.i2c_addr, reg, value)
        else:
            reg = data_all[0]
            self.bus.write_i2c_block_data(self.i2c_addr, reg, data_all[1:])

    def mem_write(self, data, memaddr):
        """Send data to specific register address (memaddr)."""
        data_all = self._convert_data(data)
        self.bus.write_i2c_block_data(self.i2c_addr, memaddr, data_all)

    def mem_read(self, length, memaddr):
        """Read data from specific register address (memaddr)."""
        return self.bus.read_i2c_block_data(self.i2c_addr, memaddr, length)

    def __init__(self, bus=1, i2c_addr=None, logger=None):
        self.logger = (
            logger if logger is not None else logging.getLogger(self.__class__.__name__)
        )
        try:
            self.bus = smbus2.SMBus(bus)
        except FileNotFoundError as e:
            self.logger.error(f"[I2CBus] I2C bus {bus} not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"[I2CBus] Failed to initialize I2C bus {bus}: {e}")
            raise
        self.i2c_addr = i2c_addr
        self.logger.info(f"[I2CBus] Initialized SMBus on bus {bus}, address {i2c_addr}")


class PinMode(Enum):
    OUT = 1
    IN = 2


class PinPull(Enum):
    PULL_UP = 17
    PULL_DOWN = 18
    PULL_NONE = 19


class Pin:
    """
    Minimal GPIO pin abstraction for input/output (BCM numbering only).

    Args:
        pin (int): BCM pin number.
        mode (PinMode): PinMode.OUT for output, PinMode.IN for input.
        pull (PinPull or None): PinPull.PULL_UP, PinPull.PULL_DOWN, or PinPull.PULL_NONE.
        active_state (bool or None): Polarity for input (optional).
    """

    def __init__(
        self,
        pin: int,
        mode: PinMode = None,
        pull: PinPull = None,
        active_state: bool = None,
    ):
        """
        Args:
            pin (int): BCM pin number.
            mode (PinMode): PinMode.OUT for output, PinMode.IN for input.
            pull (PinPull or None): PinPull.PULL_UP, PinPull.PULL_DOWN, or PinPull.PULL_NONE.
            active_state (bool or None): Polarity for input (optional).
        """
        self._pin_num = pin
        self._mode = mode
        self._pull = pull
        self._active_state = active_state
        self.gpio = None
        self.setup(mode, pull, active_state)

    def setup(self, mode: PinMode, pull: PinPull = None, active_state: bool = None):
        """
        Set up the pin mode and pull configuration. Only re-setup if mode, pull, or active_state changes.
        """
        if self.gpio is not None and (
            mode != self._mode
            or pull != self._pull
            or active_state != self._active_state
        ):
            self.gpio.close()
            self.gpio = None
        self._mode = mode
        self._pull = pull
        self._active_state = active_state
        if self.gpio is None:
            if mode in [None, PinMode.OUT]:
                self.gpio = OutputDevice(self._pin_num)
            else:
                if pull == PinPull.PULL_UP:
                    self.gpio = InputDevice(
                        self._pin_num, pull_up=True, active_state=active_state
                    )
                elif pull == PinPull.PULL_DOWN:
                    self.gpio = InputDevice(
                        self._pin_num, pull_up=False, active_state=active_state
                    )
                else:
                    self.gpio = InputDevice(
                        self._pin_num, pull_up=None, active_state=active_state
                    )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def value(self, value: int = None) -> int:
        """
        Get or set the pin value. Only allowed in output mode.
        Args:
            value (int, optional): Value to set (1 or 0). If None, returns current value.
        Returns:
            int: Current value (1 or 0).
        Raises:
            RuntimeError: If trying to set value when not in output mode.
        """
        if value is None:
            return self.gpio.value
        else:
            if self._mode != PinMode.OUT:
                raise RuntimeError(
                    "Cannot set value when pin is not in output mode. Use setup() to change mode."
                )
            if bool(value):
                self.gpio.on()
                return 1
            else:
                self.gpio.off()
                return 0

    def on(self) -> int:
        """Set pin high (only in output mode)."""
        return self.value(1)

    def off(self) -> int:
        """Set pin low (only in output mode)."""
        return self.value(0)

    def close(self):
        """Close the GPIO resource."""
        if self.gpio is not None:
            self.gpio.close()
            self.gpio = None

    def __call__(self, value: int = None) -> int:
        """Alias for value()."""
        return self.value(value)


class ADC(I2CBus):
    """
    Analog to digital converter abstraction for PiCarX (Robot Hat v4).
    Reads a value from a given ADC channel (0-7).
    """

    ADC_CHANNEL_MIN = 0
    ADC_CHANNEL_MAX = 7
    ADC_CHANNEL_OFFSET = 0x10

    @staticmethod
    def _reverse_channel(chn: int) -> int:
        """
        Reverse the channel order for hardware compatibility (see SunFounder Robot Hat v4 docs).
        """
        return ADC.ADC_CHANNEL_MAX - chn

    def __init__(self, chn: int, address: int = 0x14, bus: int = 1):
        """
        Args:
            chn (int): ADC channel (0-7, will be reversed for hardware).
            address (int): I2C address for ADC.
            bus (int): I2C bus number.
        """
        super().__init__(bus=bus, i2c_addr=address)
        if not (self.ADC_CHANNEL_MIN <= chn <= self.ADC_CHANNEL_MAX):
            raise ValueError(
                f"ADC channel should be between {self.ADC_CHANNEL_MIN} and {self.ADC_CHANNEL_MAX}, not {chn}"
            )
        chn_hw = self._reverse_channel(chn)
        self.chn = chn_hw | self.ADC_CHANNEL_OFFSET

    def read(self, length: int = 2) -> int:
        """
        Read the ADC value (hardware compatible)
        Args:
            length (int): Number of bytes to read (default 2 for ADC value)
        Returns:
            int: ADC value (0-4095)
        Raises:
            RuntimeError: If not enough bytes are read from ADC
        """
        # Write register address
        self.write([self.chn, 0, 0])
        result = super().read(length)
        if len(result) < length:
            raise RuntimeError(f"Failed to read {length} bytes from ADC, got: {result}")
        msb, lsb = result
        value = (msb << 8) + lsb
        return value

    def read_voltage(self) -> float:
        """
        Read the voltage from the ADC channel.
        Returns:
            float: Voltage value (0.0 - 3.3V)
        """
        value = self.read()
        voltage = value * 3.3 / 4095
        return voltage


class GrayscaleModule:
    """
    3-channel Grayscale Module abstraction for PiCarX (Robot Hat v4).
    Uses three ADC channels and a reference value for each channel.
    """

    REFERENCE_DEFAULT = [1000, 1000, 1000]

    def __init__(self, pin0, pin1, pin2, reference=None, logger=None):
        self.logger = (
            logger if logger is not None else logging.getLogger(self.__class__.__name__)
        )
        self.logger.info("Initializing Grayscale Module...")
        self.pins = (pin0, pin1, pin2)
        for i, pin in enumerate(self.pins):
            if not isinstance(pin, ADC):
                raise TypeError(f"pin{i} must be ADC instance")
        if reference is not None:
            # Accept both lists and numpy arrays, and convert to list of ints
            if hasattr(reference, "tolist"):
                reference = reference.tolist()
            if not (isinstance(reference, (list, tuple)) and len(reference) == 3):
                raise TypeError("reference must be a list or tuple of 3 integers")
            self._reference = [int(x) for x in reference]
        else:
            self._reference = list(self.REFERENCE_DEFAULT)

    def reference(self, ref=None):
        if ref is not None:
            if isinstance(ref, (list, tuple)) and len(ref) == 3:
                self._reference = list(ref)
            else:
                raise TypeError("ref parameter must be a list of 3 values.")
        return self._reference

    def read(self, channel=None):
        if channel is None:
            return [self.pins[i].read() for i in range(3)]
        else:
            return self.pins[channel].read()

    def read_status(self, datas=None):
        if self._reference is None:
            raise ValueError("Reference value is not set")
        if datas is None:
            datas = self.read()
        return [0 if datas[i] > self._reference[i] else 1 for i in range(3)]


class Ultrasonic:
    """
    Ultrasonic distance sensor using two GPIO pins (BCM numbering only).

    Args:
        trig (Pin): Output pin for trigger (must be Pin instance).
        echo (Pin): Input pin for echo (must be Pin instance).
        timeout (float): Timeout in seconds for echo response.
    """

    SOUND_SPEED = 343.3  # m/s

    def __init__(self, trig: "Pin", echo: "Pin", timeout: float = 0.02):
        self.logger = logging.getLogger(self.__class__.__name__)
        if not isinstance(trig, Pin):
            self.logger.error("trig must be a Pin instance")
            raise TypeError("trig must be a Pin instance")
        if not isinstance(echo, Pin):
            self.logger.error("echo must be a Pin instance")
            raise TypeError("echo must be a Pin instance")
        self.timeout = timeout
        trig.close()
        echo.close()
        # Use PinMode and PinPull enums for consistency
        self.trig = Pin(trig._pin_num, mode=PinMode.OUT)
        self.echo = Pin(echo._pin_num, mode=PinMode.IN, pull=PinPull.PULL_DOWN)
        self.logger.info(
            f"Ultrasonic sensor initialized with trig pin {self.trig._pin_num}, echo pin {self.echo._pin_num}, timeout {self.timeout}s"
        )

    def _read(self):
        """
        Perform a single ultrasonic distance measurement using monotonic timing for robustness.
        Returns:
            float: Distance in centimeters, or -1/-2 for error conditions.
        """
        self.logger.info("Starting ultrasonic measurement...")
        self.trig.off()
        time.sleep(0.001)
        self.trig.on()
        time.sleep(0.00001)
        self.trig.off()

        pulse_start = 0
        pulse_end = 0
        timeout_start = time.monotonic()

        # Wait for echo to go high
        while self.echo.gpio.value == 0:
            pulse_start = time.monotonic()
            if pulse_start - timeout_start > self.timeout:
                self.logger.info(
                    "Ultrasonic measurement timed out waiting for echo to go high."
                )
                return -1
        # Wait for echo to go low
        while self.echo.gpio.value == 1:
            pulse_end = time.monotonic()
            if pulse_end - timeout_start > self.timeout:
                self.logger.info(
                    "Ultrasonic measurement timed out waiting for echo to go low."
                )
                return -1
        if pulse_start == 0 or pulse_end == 0:
            self.logger.info("Ultrasonic measurement failed: invalid pulse timing.")
            return -2
        duration = pulse_end - pulse_start
        cm = round(duration * self.SOUND_SPEED / 2 * 100, 2)
        self.logger.info(f"Ultrasonic measurement complete: {cm} cm")
        return cm

    def read(self, times=10):
        self.logger.info(f"Reading ultrasonic sensor (up to {times} attempts)...")
        for attempt in range(times):
            a = self._read()
            if a != -1:
                self.logger.info(
                    f"Ultrasonic sensor reading succeeded on attempt {attempt+1}: {a} cm"
                )
                return a
            else:
                self.logger.info(
                    f"Ultrasonic sensor reading failed on attempt {attempt+1}"
                )
        self.logger.info(
            "Ultrasonic sensor failed to get a valid reading after all attempts."
        )
        return -1


class PWM(I2CBus):
    """
    PWM controller for Robot Hat v4 using I2C (smbus2).

    Handles setup and configuration of the PWM controller chip for both motors and servos.
    Provides base functionality for setting up frequency, clock, and resolution.

    Args:
        bus (int): I2C bus number.
        i2c_addr (int): I2C address of the PWM controller.
        freq (int): PWM frequency in Hz.
        clock (float): Clock frequency in Hz.
        pwm_res (int): PWM resolution.
        logger (logging.Logger, optional): Logger instance to use.
    """

    I2C_ADDRS = [0x14, 0x15, 0x16]
    CLOCK = 72000000.0
    PWM_RES = 4096
    DEFAULT_FREQ = 50
    _pwm_initialized = False
    _period = None

    def _set_timer_index(self, channel):
        """
        Determine the timer index for a given PWM channel.

        Args:
            channel (int): PWM channel number (0-19).

        Returns:
            int: Timer index corresponding to the channel.

        Raises:
            ValueError: If the channel is not within the valid range (0-19).
        """
        if not isinstance(channel, int) or channel < 0 or channel > 19:
            raise ValueError(
                "Invalid PWM channel: %s. Must be integer between 0 and 19." % channel
            )

        if channel < 16:
            return channel // 4
        elif channel in (16, 17):
            return 4
        elif channel == 18:
            return 5
        elif channel == 19:
            return 6

    def _setup_pwm(self, freq=None, clock=None, pwm_res=None):
        """
        Set up the PWM controller with the specified frequency, clock, and resolution.
        Returns the calculated period.
        """
        freq = freq if freq is not None else self.freq
        clock = clock if clock is not None else self.clock
        pwm_res = pwm_res if pwm_res is not None else self.pwm_res
        prescaleval = clock / (pwm_res * freq) - 1
        prescale = int(prescaleval + 0.5)
        try:
            oldmode = self.bus.read_byte_data(self.i2c_addr, 0x00)
            self.bus.write_byte_data(
                self.i2c_addr, 0x00, (oldmode & 0x7F) | 0x10
            )  # sleep
            self.bus.write_byte_data(self.i2c_addr, 0xFE, prescale)
            self.bus.write_byte_data(self.i2c_addr, 0x00, oldmode)
            time.sleep(0.005)
            self.bus.write_byte_data(
                self.i2c_addr, 0x00, oldmode | 0xA1
            )  # auto-increment on
        except Exception as e:
            self.logger.error(f"[PWM] Failed to setup PWM: {e}")
            raise
        period = int(clock / freq / (prescale + 1))
        return period

    def __init__(
        self, bus=1, i2c_addr=None, freq=None, clock=None, pwm_res=None, logger=None
    ):
        self.logger = (
            logger if logger is not None else logging.getLogger(self.__class__.__name__)
        )
        if i2c_addr is None:
            i2c_addr = self.I2C_ADDRS[0]
        I2CBus.__init__(self, bus=bus, i2c_addr=i2c_addr, logger=self.logger)
        self.freq = freq if freq is not None else self.DEFAULT_FREQ
        self.clock = clock if clock is not None else self.CLOCK
        self.pwm_res = pwm_res if pwm_res is not None else self.PWM_RES
        if not PWM._pwm_initialized:
            PWM._period = self._setup_pwm()
            PWM._pwm_initialized = True
        self.period = PWM._period
        self.logger.info(
            f"[PWM] Initialized: freq={self.freq}, clock={self.clock}, pwm_res={self.pwm_res}, i2c_addr={i2c_addr}"
        )


class DirectI2CMotor(PWM):
    """
    Direct I2C motor control for Robot Hat v4 using smbus2 for PWM and gpiozero for DIR.

    Controls a single DC motor using a PWM channel and a direction GPIO pin.
    Allows setting speed and direction, and supports reversing logic.

    Args:
        channel_pwm (int): PWM channel number for the motor.
        dir_gpio (int): GPIO pin number for direction control.
        is_reversed (bool): Whether to reverse the direction logic.
        freq (int): PWM frequency in Hz.
        i2c_addr (int): I2C address of the PWM controller.
        bus (int): I2C bus number.
        logger (logging.Logger, optional): Logger instance to use.
    """

    REG_CHN = 0x20
    REG_PSC = 0x40
    REG_ARR = 0x44

    def __init__(
        self,
        channel_pwm,
        dir_gpio,
        is_reversed=False,
        freq=PWM.DEFAULT_FREQ,
        i2c_addr=None,
        bus=1,
        logger=None,
    ):
        self.logger = (
            logger if logger is not None else logging.getLogger(self.__class__.__name__)
        )
        super().__init__(bus=bus, i2c_addr=i2c_addr, freq=freq, logger=self.logger)
        self.channel_pwm = channel_pwm
        self.dir_gpio = OutputDevice(dir_gpio)
        self._is_reversed = is_reversed
        self._speed = 0
        self.logger.info(
            f"[DirectI2CMotor] Initialized on channel {channel_pwm}, dir_gpio={dir_gpio}, is_reversed={is_reversed}, i2c_addr={i2c_addr}"
        )

    def _i2c_write(self, reg, value):
        """
        Write a 16-bit value to a given I2C register.

        Args:
            reg (int): Register address to write to.
            value (int): 16-bit value to write.
        """
        value_h = value >> 8
        value_l = value & 0xFF
        self.bus.write_i2c_block_data(self.i2c_addr, reg, [value_h, value_l])

    def speed(self, speed=None):
        """
        Set or get the motor speed.

        Args:
            speed (int, optional): Speed value from -100 to 100. If None, returns current speed.

        Returns:
            int: Current speed if no argument is given.
        """
        if speed is None:
            return self._speed
        dir_val = 1 if speed > 0 else 0
        if self._is_reversed:
            dir_val ^= 1
        abs_speed = abs(speed)
        abs_speed = max(0, min(100, abs_speed))
        pulse_width = int((abs_speed / 100.0) * self.period)
        self._i2c_write(self.REG_CHN + self.channel_pwm, pulse_width)
        if dir_val:
            self.dir_gpio.on()
        else:
            self.dir_gpio.off()
        self._speed = speed

    def set_is_reversed(self, is_reversed):
        """
        Set whether the motor direction logic is reversed.

        Args:
            is_reversed (bool): If True, reverse the direction logic.
        """
        self._is_reversed = is_reversed


class DirectI2CServo(PWM):
    """
    Direct I2C servo control for Robot Hat v4 using smbus2 for PWM.

    Provides an interface for controlling a servo motor connected to
    the PWM driver on the Robot Hat v4. Allows setting the servo angle in degrees,
    which is internally converted to the appropriate PWM pulse width.

    Args:
        channel (int): PWM channel number for the servo (0-19).
        i2c_addr (int, optional): I2C address of the PWM controller.
        bus (int, optional): I2C bus number.
        logger (logging.Logger, optional): Logger instance to use.
    """

    SERVO_MIN_US = 500
    SERVO_MAX_US = 2500
    PWM_FREQ = PWM.DEFAULT_FREQ  # Hz
    CLOCK = 72000000.0  # clock is 72MHz
    PWM_RES = 4096
    I2C_ADDRS = [0x14, 0x15, 0x16]

    def __init__(self, channel, i2c_addr=None, bus=1, logger=None):
        self.logger = (
            logger if logger is not None else logging.getLogger(self.__class__.__name__)
        )
        super().__init__(
            bus=bus,
            i2c_addr=i2c_addr,
            freq=self.PWM_FREQ,
            clock=self.CLOCK,
            pwm_res=self.PWM_RES,
            logger=self.logger,
        )
        self.channel = channel
        self.timer_index = self._set_timer_index(channel)
        self._set_period_and_prescaler()
        self._set_pwm(self.channel, 0)
        self.logger.info(
            f"[DirectI2CServo] Initialized on channel {channel}, timer_index {self.timer_index}, i2c_addr={i2c_addr}"
        )

    def _set_period_and_prescaler(self):
        """
        Configure the period and prescaler for the servo timer.
        """
        period = self.PWM_RES
        freq = self.PWM_FREQ
        clock = self.CLOCK
        prescaler = int(clock / freq / period)
        if self.timer_index < 4:
            reg_arr = 0x44 + self.timer_index
            reg_psc = 0x40 + self.timer_index
        else:
            reg_arr = 0x54 + (self.timer_index - 4)
            reg_psc = 0x50 + (self.timer_index - 4)
        arr_h = period >> 8
        arr_l = period & 0xFF
        self.bus.write_i2c_block_data(self.i2c_addr, reg_arr, [arr_h, arr_l])
        psc_h = (prescaler - 1) >> 8
        psc_l = (prescaler - 1) & 0xFF
        self.bus.write_i2c_block_data(self.i2c_addr, reg_psc, [psc_h, psc_l])

    def _setup_prescaler(self, prescaler):
        """
        Set the prescaler value for the PWM controller.

        Args:
            prescaler (int): Prescaler value to set.
        """
        self.bus.write_byte_data(self.i2c_addr, 0xFE, prescaler)

    def angle(self, degrees):
        """
        Set the servo angle in degrees.

        Args:
            degrees (float): Angle in degrees (-90 to 90).
        """
        if degrees < -90:
            degrees = -90
        if degrees > 90:
            degrees = 90
        pulse_us = self.SERVO_MIN_US + (float(degrees + 90) / 180.0) * (
            self.SERVO_MAX_US - self.SERVO_MIN_US
        )
        pulse_width_rate = pulse_us / 20000.0
        pulse = int(pulse_width_rate * self.PWM_RES)
        self.logger.debug(
            f"[DirectI2CServo] angle={degrees} pulse_us={pulse_us} pulse={pulse}"
        )
        self._set_pwm(self.channel, pulse)

    def _set_pwm(self, channel, pulse):
        """
        Set the PWM pulse width for a given channel.

        Args:
            channel (int): PWM channel number.
            pulse (int): Pulse width value.
        """
        reg = DirectI2CMotor.REG_CHN + channel
        value = min(max(pulse, 0), self.PWM_RES)
        max_retries = 5
        for attempt in range(max_retries):
            try:
                value_h = value >> 8
                value_l = value & 0xFF
                self.bus.write_i2c_block_data(self.i2c_addr, reg, [value_h, value_l])
                self.logger.debug(
                    f"[DirectI2CServo] Set PWM: channel={channel} pulse={pulse} reg=0x{reg:02X} value=0x{value:04X}"
                )
                break
            except Exception as e:
                self.logger.debug(
                    f"I2C communication error on attempt {attempt + 1}: {e}"
                )
                if attempt == max_retries - 1:
                    self.logger.error(
                        f"I2C write failed after {max_retries} attempts: {e}"
                    )

    def pulse_width(self, value):
        """
        Set the PWM pulse width directly for the servo channel.

        Args:
            value (int): Pulse width value.
        """
        self._set_pwm(self.channel, value)
