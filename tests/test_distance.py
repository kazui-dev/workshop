import unittest
from collections.abc import Callable
from unittest.mock import patch

from config import (
    LEFT_DISTANCE_ECHO_PIN,
    LEFT_DISTANCE_TRIG_PIN,
    RIGHT_DISTANCE_ECHO_PIN,
    RIGHT_DISTANCE_TRIG_PIN,
)
from distance import DistanceSensor


class FakeCallback:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


class FakePi:
    connected = True

    def __init__(
        self,
        responses: dict[int, tuple[int, int | None]],
    ) -> None:
        self.responses = responses
        self.echo_callbacks: dict[int, Callable[[int, int, int], None]] = {}
        self.callback_handles: dict[int, FakeCallback] = {}
        self.triggers: list[int] = []

    def set_mode(self, pin: int, mode: int) -> None:
        pass

    def write(self, pin: int, value: int) -> None:
        pass

    def callback(self, pin: int, edge: int, callback):
        self.echo_callbacks[pin] = callback
        handle = FakeCallback()
        self.callback_handles[pin] = handle
        return handle

    def gpio_trigger(self, pin: int, pulse_len: int, level: int) -> None:
        self.triggers.append(pin)
        echo_pin, pulse_width_us = self.responses[pin]
        if pulse_width_us is None:
            return

        echo_callback = self.echo_callbacks[echo_pin]
        echo_callback(echo_pin, 1, 1000)
        echo_callback(echo_pin, 0, 1000 + pulse_width_us)


class DistanceSensorTest(unittest.TestCase):
    def test_converts_echo_pulse_to_centimeters(self) -> None:
        self.assertAlmostEqual(
            DistanceSensor.pulse_width_to_distance_cm(1000),
            17.15,
            places=2,
        )

    def test_two_sensors_use_their_own_trigger_and_echo_pins(self) -> None:
        pi = FakePi(
            {
                LEFT_DISTANCE_TRIG_PIN: (LEFT_DISTANCE_ECHO_PIN, 1000),
                RIGHT_DISTANCE_TRIG_PIN: (RIGHT_DISTANCE_ECHO_PIN, 2000),
            }
        )
        left_sensor = DistanceSensor(
            pi,  # type: ignore[arg-type]
            trig_pin=LEFT_DISTANCE_TRIG_PIN,
            echo_pin=LEFT_DISTANCE_ECHO_PIN,
        )
        right_sensor = DistanceSensor(
            pi,  # type: ignore[arg-type]
            trig_pin=RIGHT_DISTANCE_TRIG_PIN,
            echo_pin=RIGHT_DISTANCE_ECHO_PIN,
        )

        try:
            left_distance = left_sensor.measure_distance_cm()
            right_distance = right_sensor.measure_distance_cm()
            self.assertIsNotNone(left_distance)
            self.assertIsNotNone(right_distance)
            assert left_distance is not None
            assert right_distance is not None
            self.assertAlmostEqual(left_distance, 17.15)
            self.assertAlmostEqual(right_distance, 34.3)
            self.assertEqual(
                pi.triggers,
                [LEFT_DISTANCE_TRIG_PIN, RIGHT_DISTANCE_TRIG_PIN],
            )
            self.assertEqual(
                set(pi.echo_callbacks),
                {LEFT_DISTANCE_ECHO_PIN, RIGHT_DISTANCE_ECHO_PIN},
            )
        finally:
            left_sensor.close()
            right_sensor.close()

        self.assertTrue(pi.callback_handles[LEFT_DISTANCE_ECHO_PIN].cancelled)
        self.assertTrue(pi.callback_handles[RIGHT_DISTANCE_ECHO_PIN].cancelled)

    def test_returns_none_on_timeout(self) -> None:
        pi = FakePi({LEFT_DISTANCE_TRIG_PIN: (LEFT_DISTANCE_ECHO_PIN, None)})
        with DistanceSensor(
            pi,  # type: ignore[arg-type]
            trig_pin=LEFT_DISTANCE_TRIG_PIN,
            echo_pin=LEFT_DISTANCE_ECHO_PIN,
        ) as sensor:
            with patch("distance.DISTANCE_TIMEOUT_SECONDS", 0):
                self.assertIsNone(sensor.measure_distance_cm())

    def test_returns_none_for_out_of_range_pulse(self) -> None:
        pi = FakePi({LEFT_DISTANCE_TRIG_PIN: (LEFT_DISTANCE_ECHO_PIN, 1)})
        with DistanceSensor(
            pi,  # type: ignore[arg-type]
            trig_pin=LEFT_DISTANCE_TRIG_PIN,
            echo_pin=LEFT_DISTANCE_ECHO_PIN,
        ) as sensor:
            self.assertIsNone(sensor.measure_distance_cm())


if __name__ == "__main__":
    unittest.main()
