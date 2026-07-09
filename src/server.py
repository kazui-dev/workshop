import json
import logging
from collections.abc import Callable

from websockets.asyncio.server import serve

from config import PWM_MAX, PWM_MIN, WEBSOCKET_HOST, WEBSOCKET_PORT

logger = logging.getLogger(__name__)


def _parse_operation_message(message) -> tuple[int, int]:
    try:
        payload = json.loads(message)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("message must be valid JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("message must be a JSON object")

    if "left" not in payload or "right" not in payload:
        raise ValueError("message must contain left and right")

    left = payload["left"]
    right = payload["right"]

    if (
        isinstance(left, bool)
        or not isinstance(left, int)
        or isinstance(right, bool)
        or not isinstance(right, int)
    ):
        raise ValueError("left and right must be integers")

    if not PWM_MIN <= left <= PWM_MAX or not PWM_MIN <= right <= PWM_MAX:
        raise ValueError(
            f"left and right must be between {PWM_MIN} and {PWM_MAX}"
        )

    return left, right


class OperationServer:
    def __init__(self, set_pwm: Callable[[int, int], None]) -> None:
        self._set_pwm = set_pwm

    async def handle_connection(self, websocket) -> None:
        remote_address = websocket.remote_address
        logger.info("WebSocket client connected: %s", remote_address)

        try:
            async for message in websocket:
                try:
                    left, right = _parse_operation_message(message)
                except ValueError as exc:
                    logger.warning(
                        "Ignoring invalid operation message from %s: %s",
                        remote_address,
                        exc,
                    )
                    continue

                self._set_pwm(left, right)
        finally:
            logger.info("WebSocket client disconnected: %s", remote_address)

    async def run(self) -> None:
        logger.info("Starting server on %s:%d", WEBSOCKET_HOST, WEBSOCKET_PORT)
        async with serve(self.handle_connection, WEBSOCKET_HOST, WEBSOCKET_PORT) as server:
            await server.serve_forever()
