from __future__ import annotations

import threading
from types import TracebackType

import pigpio

from config import (
    DISTANCE_MAX_CM,
    DISTANCE_MIN_CM,
    DISTANCE_TIMEOUT_SECONDS,
)

SPEED_OF_SOUND_CM_PER_SECOND = 34300.0


class DistanceSensor:
    """Measure HC-SR04 echo pulses using pigpiod edge timestamps."""

    def __init__(
        self,
        pi: pigpio.pi | None = None,
        *,
        trig_pin: int,
        echo_pin: int,
    ) -> None:
        self._pi = pi if pi is not None else pigpio.pi()
        self._owns_connection = pi is None
        self._trig_pin = trig_pin
        self._echo_pin = echo_pin
        self._closed = False
        self._measurement_lock = threading.Lock()
        self._echo_received = threading.Event()
        self._rising_tick: int | None = None
        self._pulse_width_us: int | None = None

        if not self._pi.connected:
            if self._owns_connection:
                self._pi.stop()
            raise RuntimeError(
                "Failed to connect to pigpiod.\n"
                "Please start pigpiod by running 'sudo pigpiod'."
            )

        try:
            self._pi.set_mode(self._trig_pin, pigpio.OUTPUT)
            self._pi.set_mode(self._echo_pin, pigpio.INPUT)
            self._pi.write(self._trig_pin, 0)
            self._callback = self._pi.callback(
                self._echo_pin,
                pigpio.EITHER_EDGE,
                self._handle_echo_edge,
            )
        except Exception:
            if self._owns_connection:
                self._pi.stop()
            self._closed = True
            raise

    def __enter__(self) -> DistanceSensor:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _handle_echo_edge(self, gpio: int, level: int, tick: int) -> None:
        if gpio != self._echo_pin:
            return

        if level == 1:
            self._rising_tick = tick
            return

        if level == 0 and self._rising_tick is not None:
            self._pulse_width_us = pigpio.tickDiff(self._rising_tick, tick)
            self._rising_tick = None
            self._echo_received.set()

    @staticmethod
    def pulse_width_to_distance_cm(pulse_width_us: int) -> float:
        round_trip_seconds = pulse_width_us / 1_000_000
        return round_trip_seconds * SPEED_OF_SOUND_CM_PER_SECOND / 2

    def measure_distance_cm(self) -> float | None:
        """Return a distance in cm, or None for timeout/out-of-range data."""
        if self._closed:
            raise RuntimeError("DistanceSensor is closed")

        with self._measurement_lock:
            self._rising_tick = None
            self._pulse_width_us = None
            self._echo_received.clear()
            self._pi.gpio_trigger(self._trig_pin, 10, 1)

            if not self._echo_received.wait(DISTANCE_TIMEOUT_SECONDS):
                return None

            if self._pulse_width_us is None:
                return None

            distance_cm = self.pulse_width_to_distance_cm(self._pulse_width_us)
            if not DISTANCE_MIN_CM <= distance_cm <= DISTANCE_MAX_CM:
                return None
            return distance_cm

    def close(self) -> None:
        if self._closed:
            return

        try:
            self._callback.cancel()
        finally:
            if self._owns_connection:
                self._pi.stop()
            self._closed = True
