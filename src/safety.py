from __future__ import annotations

from typing import Protocol

from config import (
    DISTANCE_INVALID_LIMIT,
    DISTANCE_SENSOR_IDS,
    OBSTACLE_CLEAR_DISTANCE_CM,
    OBSTACLE_DISTANCE_CM,
)


class _DistanceState:
    def __init__(self) -> None:
        self.obstacle_detected = False
        self.invalid_count = 0


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
        sensor_ids: tuple[str, ...] = DISTANCE_SENSOR_IDS,
    ) -> None:
        if not sensor_ids:
            raise ValueError("at least one distance sensor is required")

        self._motor = motor
        self._buzzer = buzzer
        self._obstacle_detected = False
        self._distance_states = {
            sensor_id: _DistanceState() for sensor_id in sensor_ids
        }

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

    def update_distance(self, sensor_id: str, distance_cm: float | None) -> None:
        try:
            state = self._distance_states[sensor_id]
        except KeyError as exc:
            raise ValueError(f"unknown distance sensor: {sensor_id}") from exc

        if distance_cm is None:
            state.invalid_count += 1
            if state.invalid_count >= DISTANCE_INVALID_LIMIT:
                state.obstacle_detected = True
        else:
            state.invalid_count = 0
            if state.obstacle_detected:
                state.obstacle_detected = distance_cm < OBSTACLE_CLEAR_DISTANCE_CM
            else:
                state.obstacle_detected = distance_cm <= OBSTACLE_DISTANCE_CM

        self._set_obstacle_detected(
            any(
                sensor_state.obstacle_detected
                for sensor_state in self._distance_states.values()
            )
        )

    def _set_obstacle_detected(self, obstacle_detected: bool) -> None:
        if obstacle_detected == self._obstacle_detected:
            return

        self._obstacle_detected = obstacle_detected
        if obstacle_detected:
            # Require a fresh clear reading from every sensor before releasing
            # the global safety latch, including sensors that were previously
            # between the detection and clear thresholds.
            for state in self._distance_states.values():
                state.obstacle_detected = True
            self._motor.stop()
            self._buzzer.start()
        else:
            self._buzzer.stop()
