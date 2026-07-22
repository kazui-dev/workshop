import unittest
from unittest.mock import patch

from config import DISTANCE_ECHO_PIN
from distance import DistanceSensor


class FakeCallback:
    def cancel(self) -> None:
        pass


class FakePi:
    connected = True

    def __init__(self, pulse_width_us: int | None) -> None:
        self.pulse_width_us = pulse_width_us
        self.echo_callback = None

    def set_mode(self, pin: int, mode: int) -> None:
        pass

    def write(self, pin: int, value: int) -> None:
        pass

    def callback(self, pin: int, edge: int, callback):
        self.echo_callback = callback
        return FakeCallback()

    def gpio_trigger(self, pin: int, pulse_len: int, level: int) -> None:
        if self.pulse_width_us is None:
            return
        assert self.echo_callback is not None
        self.echo_callback(DISTANCE_ECHO_PIN, 1, 1000)
        self.echo_callback(
            DISTANCE_ECHO_PIN,
            0,
            1000 + self.pulse_width_us,
        )


class DistanceSensorTest(unittest.TestCase):
    def test_converts_echo_pulse_to_centimeters(self) -> None:
        self.assertAlmostEqual(
            DistanceSensor.pulse_width_to_distance_cm(1000),
            17.15,
            places=2,
        )

    def test_measures_distance_from_echo_edges(self) -> None:
        sensor = DistanceSensor(FakePi(1000))  # type: ignore[arg-type]
        distance_cm = sensor.measure_distance_cm()
        self.assertIsNotNone(distance_cm)
        assert distance_cm is not None
        self.assertAlmostEqual(distance_cm, 17.15, places=2)

    def test_returns_none_on_timeout(self) -> None:
        sensor = DistanceSensor(FakePi(None))  # type: ignore[arg-type]
        with patch("distance.DISTANCE_TIMEOUT_SECONDS", 0):
            self.assertIsNone(sensor.measure_distance_cm())

    def test_returns_none_for_out_of_range_pulse(self) -> None:
        sensor = DistanceSensor(FakePi(1))  # type: ignore[arg-type]
        self.assertIsNone(sensor.measure_distance_cm())


if __name__ == "__main__":
    unittest.main()
