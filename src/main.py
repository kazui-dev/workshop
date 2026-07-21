import asyncio
import logging

from motor import MotorDriver
from server import OperationServer

logger = logging.getLogger(__name__)


async def main() -> None:
    with MotorDriver() as motor:
        server = OperationServer(motor)
        await server.run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped")
