import asyncio
import logging

from server import OperationServer

logger = logging.getLogger(__name__)


def log_pwm(left: int, right: int) -> None:
    logger.info("Motor command: left=%d right=%d", left, right)


async def main() -> None:
    server = OperationServer(log_pwm)
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
