import pigpio

from config import (
    LEFT_DIR_PIN,
    LEFT_PWM_PIN,
    RIGHT_DIR_PIN,
    RIGHT_PWM_PIN,
    PWM_RANGE,
    PWM_FREQUENCY,
    LEFT_REVERSE,
    RIGHT_REVERSE,
)


class MotorDriver:
    def __init__(self):
        self.pi = pigpio.pi()

        if not self.pi.connected:
            raise RuntimeError(
                "Failed to connect to pigpiod.\n"
                "Please start pigpiod by running 'sudo pigpiod'."
            )

        # Configure all GPIO pins as outputs
        for pin in (
            LEFT_PWM_PIN,
            RIGHT_PWM_PIN,
            LEFT_DIR_PIN,
            RIGHT_DIR_PIN,
        ):
            self.pi.set_mode(pin, pigpio.OUTPUT)

        # Configure PWM settings
        for pin in (LEFT_PWM_PIN, RIGHT_PWM_PIN):
            self.pi.set_PWM_range(pin, PWM_RANGE)
            self.pi.set_PWM_frequency(pin, PWM_FREQUENCY)

    def _set_motor(self, pwm_pin, dir_pin, value, reverse):
        value = max(-PWM_RANGE, min(PWM_RANGE, value))

        forward = value >= 0

        if reverse:
            forward = not forward

        self.pi.write(dir_pin, int(forward))
        self.pi.set_PWM_dutycycle(pwm_pin, abs(value))

    def set_pwm(self, left: int, right: int):
        self._set_motor(
            LEFT_PWM_PIN,
            LEFT_DIR_PIN,
            left,
            LEFT_REVERSE,
        )

        self._set_motor(
            RIGHT_PWM_PIN,
            RIGHT_DIR_PIN,
            right,
            RIGHT_REVERSE,
        )

    def stop(self):
        self.set_pwm(0, 0)

    def close(self):
        self.stop()
        self.pi.stop()