from __future__ import annotations

from typing import Protocol

from config import OBSTACLE_DISTANCE_CM


class MotorController(Protocol):
    def set_pwm(self, left: int, right: int) -> None: ...

    def stop(self) -> None: ...


class WarningController(Protocol):
    def start(self) -> None: ...

    def stop(self) -> None: ...


class SafetyController:
    def __init__(
        self,
        motor: MotorController,
        buzzer: WarningController,
    ) -> None:
        self._motor = motor
        self._buzzer = buzzer
        self._obstacle_detected = False

    @property
    def obstacle_detected(self) -> bool:
        return self._obstacle_detected

    @staticmethod
    def remove_forward_component(left: int, right: int) -> tuple[int, int]:
        """Keep reverse/rotation while removing forward translation."""
        forward_component = (left + right) / 2
        if forward_component <= 0:
            return left, right

        return round(left - forward_component), round(right - forward_component)

    def apply_operation(self, left: int, right: int) -> None:
        if self._obstacle_detected:
            left, right = self.remove_forward_component(left, right)
        self._motor.set_pwm(left, right)

    def communication_timeout(self) -> None:
        self._motor.stop()

    def disconnected(self) -> None:
        self._motor.stop()

    def update_distance(self, distance_cm: float | None) -> None:
        if distance_cm is None:
            return

        obstacle_detected = distance_cm <= OBSTACLE_DISTANCE_CM
        if obstacle_detected == self._obstacle_detected:
            return

        self._obstacle_detected = obstacle_detected
        if obstacle_detected:
            self._motor.stop()
            self._buzzer.start()
        else:
            self._buzzer.stop()
