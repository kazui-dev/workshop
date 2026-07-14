from __future__ import annotations

import asyncio
import json
import logging
from typing import Protocol

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from config import (
    OPERATION_TIMEOUT_SECONDS,
    PWM_MAX,
    PWM_MIN,
    WEBSOCKET_HOST,
    WEBSOCKET_PORT,
)

logger = logging.getLogger(__name__)


class MotorController(Protocol):
    def set_pwm(self, left: int, right: int) -> None: ...

    def stop(self) -> None: ...


def _parse_operation_message(message: str | bytes) -> tuple[int, int]:
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
        raise ValueError(f"left and right must be between {PWM_MIN} and {PWM_MAX}")

    return left, right


class OperationServer:
    def __init__(self, motor: MotorController) -> None:
        self._motor = motor
        self._active_connection: ServerConnection | None = None

    async def handle_connection(self, websocket: ServerConnection) -> None:
        remote_address = websocket.remote_address

        if self._active_connection is not None:
            logger.warning(
                "Rejecting additional WebSocket client: %s",
                remote_address,
            )
            await websocket.close(
                code=1013,
                reason="Another client is controlling the motors",
            )
            return

        self._active_connection = websocket
        logger.info("WebSocket client connected: %s", remote_address)
        loop = asyncio.get_running_loop()
        operation_deadline: float | None = None

        try:
            while True:
                try:
                    if operation_deadline is None:
                        message = await websocket.recv()
                    else:
                        remaining = max(0.0, operation_deadline - loop.time())
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=remaining,
                        )
                except TimeoutError:
                    logger.warning(
                        "No operation message from %s for %.0fms; stopping motors",
                        remote_address,
                        OPERATION_TIMEOUT_SECONDS * 1000,
                    )
                    self._motor.stop()
                    operation_deadline = None
                    continue
                except ConnectionClosed:
                    break

                try:
                    left, right = _parse_operation_message(message)
                except ValueError as exc:
                    logger.warning(
                        "Ignoring invalid operation message from %s: %s",
                        remote_address,
                        exc,
                    )
                    continue

                self._motor.set_pwm(left, right)
                operation_deadline = loop.time() + OPERATION_TIMEOUT_SECONDS
        finally:
            try:
                self._motor.stop()
            finally:
                self._active_connection = None
                logger.info(
                    "WebSocket client disconnected: %s",
                    remote_address,
                )

    async def run(self) -> None:
        logger.info("Starting server on %s:%d", WEBSOCKET_HOST, WEBSOCKET_PORT)
        async with serve(
            self.handle_connection,
            WEBSOCKET_HOST,
            WEBSOCKET_PORT,
        ) as server:
            await server.serve_forever()
