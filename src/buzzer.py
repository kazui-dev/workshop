from __future__ import annotations

from types import TracebackType

import pigpio

from config import BUZZER_DUTY_CYCLE, BUZZER_FREQUENCY, BUZZER_PIN


class Buzzer:
    def __init__(self, pi: pigpio.pi | None = None) -> None:
        self._pi = pi if pi is not None else pigpio.pi()
        self._owns_connection = pi is None
        self._active = False
        self._closed = False
        self._initialized = False

        if not self._pi.connected:
            if self._owns_connection:
                self._pi.stop()
            raise RuntimeError(
                "Failed to connect to pigpiod.\n"
                "Please start pigpiod by running 'sudo pigpiod'."
            )

        try:
            self._pi.set_mode(BUZZER_PIN, pigpio.OUTPUT)
            self._pi.set_PWM_range(BUZZER_PIN, 255)
            self.stop()
        except Exception:
            if self._owns_connection:
                self._pi.stop()
            self._closed = True
            raise

    def __enter__(self) -> Buzzer:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def start(self) -> None:
        if self._closed:
            raise RuntimeError("Buzzer is closed")
        if self._active:
            return

        self._pi.set_PWM_frequency(BUZZER_PIN, BUZZER_FREQUENCY)
        self._pi.set_PWM_dutycycle(BUZZER_PIN, BUZZER_DUTY_CYCLE)
        self._active = True

    def stop(self) -> None:
        if self._closed:
            raise RuntimeError("Buzzer is closed")
        if not self._active and self._initialized:
            return

        self._pi.set_PWM_dutycycle(BUZZER_PIN, 0)
        self._active = False
        self._initialized = True

    def close(self) -> None:
        if self._closed:
            return

        try:
            self.stop()
        finally:
            if self._owns_connection:
                self._pi.stop()
            self._closed = True
