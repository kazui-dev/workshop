import asyncio
import logging

from server import OperationServer
from motor import MotorDriver

logger = logging.getLogger(__name__)

async def main() -> None:
    motor = MotorDriver()

    server = OperationServer(motor.set_pwm)

    try:
        await server.run()
    finally:
        motor.close()
    
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped")
