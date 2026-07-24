import asyncio
import logging
import os
from contextlib import ExitStack

import pigpio

from config import DISTANCE_MEASUREMENT_INTERVAL_SECONDS, DISTANCE_SENSOR_PINS
from distance import DistanceSensor
from motor import MotorDriver
from safety import SafetyController
from server import OperationServer

logger = logging.getLogger(__name__)


async def monitor_distances(
    distance_sensors: tuple[tuple[str, DistanceSensor], ...],
    safety: SafetyController,
) -> None:
    while True:
        for sensor_id, distance_sensor in distance_sensors:
            distance_cm = await asyncio.to_thread(distance_sensor.measure_distance_cm)
            safety.update_distance(sensor_id, distance_cm)
            await asyncio.sleep(DISTANCE_MEASUREMENT_INTERVAL_SECONDS)


async def main() -> None:
    pi = pigpio.pi()
    if not pi.connected:
        pi.stop()
        raise RuntimeError(
            "Failed to connect to pigpiod.\n"
            "Please start pigpiod by running 'sudo pigpiod'."
        )

    try:
        with ExitStack() as stack:
            motor = stack.enter_context(MotorDriver(pi))
            distance_sensors = tuple(
                (
                    sensor_id,
                    stack.enter_context(
                        DistanceSensor(
                            pi,
                            trig_pin=trig_pin,
                            echo_pin=echo_pin,
                        )
                    ),
                )
                for sensor_id, trig_pin, echo_pin in DISTANCE_SENSOR_PINS
            )
            safety = SafetyController(motor)
            server = OperationServer(safety)
            server_task = asyncio.create_task(server.run())
            monitor_task = asyncio.create_task(
                monitor_distances(distance_sensors, safety)
            )
            tasks = (server_task, monitor_task)
            try:
                done, _ = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_EXCEPTION,
                )
                for task in done:
                    task.result()
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        pi.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("server").setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped")
