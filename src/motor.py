from __future__ import annotations

import logging
from types import TracebackType

import pigpio

from config import (
    LEFT_DIR_PIN,
    LEFT_PWM_PIN,
    LEFT_REVERSE,
    PWM_FREQUENCY,
    PWM_RANGE,
    RIGHT_DIR_PIN,
    RIGHT_PWM_PIN,
    RIGHT_REVERSE,
)

logger = logging.getLogger(__name__)

PWM_PINS = (LEFT_PWM_PIN, RIGHT_PWM_PIN)
OUTPUT_PINS = PWM_PINS + (LEFT_DIR_PIN, RIGHT_DIR_PIN)


class MotorDriver:
    def __init__(self) -> None:
        self._pi = pigpio.pi()
        self._closed = False
        self._direction_by_pin: dict[int, bool] = {}

        if not self._pi.connected:
            self._pi.stop()
            raise RuntimeError(
                "Failed to connect to pigpiod.\n"
                "Please start pigpiod by running 'sudo pigpiod'."
            )

        try:
            # Clear any PWM state left in the long-running pigpiod process.
            self.stop()
            self._configure_gpio()
            self.stop()
        except Exception:
            self._pi.stop()
            self._closed = True
            raise

    def __enter__(self) -> MotorDriver:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _configure_gpio(self) -> None:
        for pin in OUTPUT_PINS:
            self._pi.set_mode(pin, pigpio.OUTPUT)

        for pin in PWM_PINS:
            self._pi.set_PWM_range(pin, PWM_RANGE)
            self._pi.set_PWM_frequency(pin, PWM_FREQUENCY)

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("MotorDriver is closed")

    def _set_motor(
        self,
        pwm_pin: int,
        dir_pin: int,
        value: int,
        reverse: bool,
    ) -> None:
        value = max(-PWM_RANGE, min(PWM_RANGE, value))

        if value == 0:
            self._pi.set_PWM_dutycycle(pwm_pin, 0)
            return

        forward = (value > 0) != reverse

        if self._direction_by_pin.get(dir_pin) != forward:
            # Remove drive power before changing direction.
            self._pi.set_PWM_dutycycle(pwm_pin, 0)
            self._pi.write(dir_pin, int(forward))
            self._direction_by_pin[dir_pin] = forward

        self._pi.set_PWM_dutycycle(pwm_pin, abs(value))

    def set_pwm(self, left: int, right: int) -> None:
        self._ensure_open()

        try:
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
        except Exception:
            try:
                self.stop()
            except Exception:
                logger.exception("Failed to stop motors after a GPIO error")
            raise

    def stop(self) -> None:
        self._ensure_open()
        first_error: Exception | None = None

        for pin in PWM_PINS:
            try:
                self._pi.set_PWM_dutycycle(pin, 0)
            except Exception as exc:
                if first_error is None:
                    first_error = exc

        if first_error is not None:
            raise first_error

    def close(self) -> None:
        if self._closed:
            return

        try:
            self.stop()
        finally:
            self._pi.stop()
            self._closed = True
