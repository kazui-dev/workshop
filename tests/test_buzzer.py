import unittest

from buzzer import Buzzer
from config import BUZZER_DUTY_CYCLE, BUZZER_PIN


class FakePi:
    connected = True

    def __init__(self) -> None:
        self.duty_cycles: list[tuple[int, int]] = []
        self.frequencies: list[tuple[int, int]] = []

    def set_mode(self, pin: int, mode: int) -> None:
        pass

    def set_PWM_range(self, pin: int, pwm_range: int) -> None:
        pass

    def set_PWM_frequency(self, pin: int, frequency: int) -> None:
        self.frequencies.append((pin, frequency))

    def set_PWM_dutycycle(self, pin: int, duty_cycle: int) -> None:
        self.duty_cycles.append((pin, duty_cycle))


class BuzzerTest(unittest.TestCase):
    def test_start_and_stop_are_idempotent(self) -> None:
        pi = FakePi()
        buzzer = Buzzer(pi)  # type: ignore[arg-type]

        buzzer.start()
        buzzer.start()
        buzzer.stop()
        buzzer.stop()

        self.assertEqual(pi.duty_cycles, [(BUZZER_PIN, 0), (BUZZER_PIN, BUZZER_DUTY_CYCLE), (BUZZER_PIN, 0)])
        self.assertEqual(len(pi.frequencies), 1)


if __name__ == "__main__":
    unittest.main()
