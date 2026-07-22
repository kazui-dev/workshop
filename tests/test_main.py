import asyncio
import unittest
from unittest.mock import patch

from main import monitor_distances


class FakeDistanceSensor:
    def __init__(self, sensor_id: str, distance_cm: float) -> None:
        self.sensor_id = sensor_id
        self.distance_cm = distance_cm
        self.measurements: list[str] = []

    def measure_distance_cm(self) -> float:
        self.measurements.append(self.sensor_id)
        return self.distance_cm


class FakeSafety:
    def __init__(self) -> None:
        self.updates: list[tuple[str, float | None]] = []
        self.enough_updates = asyncio.Event()

    def update_distance(
        self,
        sensor_id: str,
        distance_cm: float | None,
    ) -> None:
        self.updates.append((sensor_id, distance_cm))
        if len(self.updates) >= 4:
            self.enough_updates.set()


class MonitorDistancesTest(unittest.IsolatedAsyncioTestCase):
    async def test_measures_sensors_sequentially(self) -> None:
        left = FakeDistanceSensor("left", 10)
        right = FakeDistanceSensor("right", 30)
        safety = FakeSafety()

        with patch("main.DISTANCE_MEASUREMENT_INTERVAL_SECONDS", 0):
            task = asyncio.create_task(
                monitor_distances(
                    (
                        ("left", left),  # type: ignore[arg-type]
                        ("right", right),  # type: ignore[arg-type]
                    ),
                    safety,  # type: ignore[arg-type]
                )
            )
            await asyncio.wait_for(safety.enough_updates.wait(), timeout=1)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        self.assertEqual(
            safety.updates[:4],
            [("left", 10), ("right", 30), ("left", 10), ("right", 30)],
        )


if __name__ == "__main__":
    unittest.main()
