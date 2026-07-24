import unittest

from config import (
    DISTANCE_INVALID_LIMIT,
    OBSTACLE_CLEAR_DISTANCE_CM,
    OBSTACLE_DISTANCE_CM,
)
from safety import SafetyController


class FakeMotor:
    def __init__(self) -> None:
        self.operations: list[tuple[int, int]] = []
        self.stop_count = 0

    def set_pwm(self, left: int, right: int) -> None:
        self.operations.append((left, right))

    def stop(self) -> None:
        self.stop_count += 1


class SafetyControllerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.motor = FakeMotor()
        self.safety = SafetyController(self.motor)

    def test_timeout_and_disconnect_stop_motors(self) -> None:
        self.safety.communication_timeout()
        self.safety.disconnected()
        self.assertEqual(self.motor.stop_count, 2)

    def test_forward_is_blocked_until_all_sensors_report_clear(self) -> None:
        self.safety.apply_operation(100, 100)
        self.safety.update_distance("left", OBSTACLE_CLEAR_DISTANCE_CM)
        self.safety.update_distance("right", OBSTACLE_CLEAR_DISTANCE_CM - 1)
        self.safety.apply_operation(100, 100)
        self.safety.update_distance("right", OBSTACLE_CLEAR_DISTANCE_CM)
        self.safety.apply_operation(100, 100)

        self.assertEqual(self.motor.operations, [(0, 0), (0, 0), (100, 100)])

    def test_startup_interlock_allows_reverse_and_rotation(self) -> None:
        self.safety.apply_operation(-100, -100)
        self.safety.apply_operation(100, -100)

        self.assertEqual(self.motor.operations, [(-100, -100), (100, -100)])

    def test_obstacle_stops_motor_once(self) -> None:
        self.safety.update_distance("left", OBSTACLE_DISTANCE_CM)
        self.safety.update_distance("left", OBSTACLE_DISTANCE_CM - 1)
        self.assertTrue(self.safety.obstacle_detected)
        self.assertEqual(self.motor.stop_count, 1)

    def test_clearing_obstacle_restores_operation(self) -> None:
        self.safety.update_distance("left", OBSTACLE_DISTANCE_CM - 1)
        self.safety.update_distance("left", OBSTACLE_CLEAR_DISTANCE_CM)
        self.safety.update_distance("right", OBSTACLE_CLEAR_DISTANCE_CM)
        self.safety.apply_operation(100, 100)
        self.assertFalse(self.safety.obstacle_detected)
        self.assertEqual(self.motor.operations, [(100, 100)])

    def test_obstacle_state_uses_clear_distance_hysteresis(self) -> None:
        self.safety.update_distance("left", OBSTACLE_DISTANCE_CM)
        self.safety.update_distance("left", OBSTACLE_DISTANCE_CM + 1)
        self.assertTrue(self.safety.obstacle_detected)

        self.safety.update_distance("left", OBSTACLE_CLEAR_DISTANCE_CM)
        self.safety.update_distance("right", OBSTACLE_CLEAR_DISTANCE_CM)
        self.assertFalse(self.safety.obstacle_detected)

    def test_obstacle_removes_forward_but_keeps_rotation(self) -> None:
        self.safety.update_distance("left", OBSTACLE_DISTANCE_CM - 1)
        self.safety.apply_operation(200, 100)
        self.assertEqual(self.motor.operations, [(50, -50)])

    def test_obstacle_allows_reverse_and_in_place_rotation(self) -> None:
        self.safety.update_distance("left", OBSTACLE_DISTANCE_CM - 1)
        self.safety.apply_operation(-100, -100)
        self.safety.apply_operation(100, -100)
        self.assertEqual(self.motor.operations, [(-100, -100), (100, -100)])

    def test_repeated_invalid_distance_stops_as_sensor_fault(self) -> None:
        for _ in range(DISTANCE_INVALID_LIMIT - 1):
            self.safety.update_distance("left", None)

        self.assertFalse(self.safety.obstacle_detected)
        self.assertEqual(self.motor.stop_count, 0)

        self.safety.update_distance("left", None)
        self.assertTrue(self.safety.obstacle_detected)
        self.assertEqual(self.motor.stop_count, 1)

    def test_valid_distance_resets_invalid_distance_count(self) -> None:
        for _ in range(DISTANCE_INVALID_LIMIT - 1):
            self.safety.update_distance("left", None)

        self.safety.update_distance("left", OBSTACLE_CLEAR_DISTANCE_CM)
        self.safety.update_distance("left", None)
        self.assertFalse(self.safety.obstacle_detected)
        self.assertEqual(self.motor.stop_count, 0)

    def test_one_clear_sensor_does_not_clear_the_other_obstacle(self) -> None:
        self.safety.update_distance("left", OBSTACLE_DISTANCE_CM - 1)
        self.safety.update_distance("right", OBSTACLE_DISTANCE_CM - 1)

        self.safety.update_distance("left", OBSTACLE_CLEAR_DISTANCE_CM)
        self.assertTrue(self.safety.obstacle_detected)

        self.safety.update_distance("right", OBSTACLE_CLEAR_DISTANCE_CM)
        self.assertFalse(self.safety.obstacle_detected)

    def test_all_sensors_must_reach_clear_distance_after_detection(self) -> None:
        self.safety.update_distance("right", OBSTACLE_DISTANCE_CM + 1)
        self.safety.update_distance("left", OBSTACLE_DISTANCE_CM)

        self.safety.update_distance("left", OBSTACLE_CLEAR_DISTANCE_CM)
        self.assertTrue(self.safety.obstacle_detected)

        self.safety.update_distance("right", OBSTACLE_CLEAR_DISTANCE_CM)
        self.assertFalse(self.safety.obstacle_detected)

    def test_valid_sensor_does_not_reset_other_sensor_fault_count(self) -> None:
        for _ in range(DISTANCE_INVALID_LIMIT):
            self.safety.update_distance("left", None)
            self.safety.update_distance("right", OBSTACLE_CLEAR_DISTANCE_CM)

        self.assertTrue(self.safety.obstacle_detected)
        self.assertEqual(self.motor.stop_count, 1)

    def test_rejects_unknown_sensor(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown distance sensor"):
            self.safety.update_distance("rear", 100)


if __name__ == "__main__":
    unittest.main()
