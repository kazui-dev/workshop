import asyncio
import logging
import os

import pigpio

from buzzer import Buzzer
from config import DISTANCE_MEASUREMENT_INTERVAL_SECONDS
from distance import DistanceSensor
from motor import MotorDriver
from safety import SafetyController
from server import OperationServer

logger = logging.getLogger(__name__)


async def monitor_distance(
    distance_sensor: DistanceSensor,
    safety: SafetyController,
) -> None:
    while True:
        distance_cm = await asyncio.to_thread(distance_sensor.measure_distance_cm)
        safety.update_distance(distance_cm)
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
        with (
            MotorDriver(pi) as motor,
            DistanceSensor(pi) as distance_sensor,
            Buzzer(pi) as buzzer,
        ):
            safety = SafetyController(motor, buzzer)
            server = OperationServer(safety)
            server_task = asyncio.create_task(server.run())
            monitor_task = asyncio.create_task(
                monitor_distance(distance_sensor, safety)
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
    logging.getLogger("server").setLevel(
        os.environ.get("LOG_LEVEL", "INFO").upper()
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped")
