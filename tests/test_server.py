import asyncio
import unittest

from config import OPERATION_TIMEOUT_SECONDS
from server import OperationServer, _parse_operation_message


class FakeController:
    def __init__(self) -> None:
        self.operations: list[tuple[int, int]] = []
        self.timeout_called = asyncio.Event()
        self.disconnected_called = False

    def apply_operation(self, left: int, right: int) -> None:
        self.operations.append((left, right))

    def communication_timeout(self) -> None:
        self.timeout_called.set()

    def disconnected(self) -> None:
        self.disconnected_called = True


class FakeWebSocket:
    remote_address = ("127.0.0.1", 12345)

    def __init__(self, messages: list[str]) -> None:
        self.messages = iter(messages)

    async def recv(self) -> str:
        try:
            return next(self.messages)
        except StopIteration:
            pass

        await asyncio.Event().wait()
        raise AssertionError("unreachable")


class ParseOperationMessageTest(unittest.TestCase):
    def test_accepts_valid_pwm_values(self) -> None:
        self.assertEqual(
            _parse_operation_message(
                '{"leftMotorPwm": 10, "rightMotorPwm": -20}'
            ),
            (10, -20),
        )

    def test_rejects_boolean_values(self) -> None:
        with self.assertRaises(ValueError):
            _parse_operation_message(
                '{"leftMotorPwm": true, "rightMotorPwm": 0}'
            )

    def test_rejects_out_of_range_values(self) -> None:
        with self.assertRaises(ValueError):
            _parse_operation_message(
                '{"leftMotorPwm": 256, "rightMotorPwm": 0}'
            )


class OperationServerTest(unittest.IsolatedAsyncioTestCase):
    async def test_operation_timeout_is_handled_without_escaping(self) -> None:
        controller = FakeController()
        server = OperationServer(controller)
        websocket = FakeWebSocket(
            ['{"leftMotorPwm": 10, "rightMotorPwm": -20}']
        )

        task = asyncio.create_task(server.handle_connection(websocket))  # type: ignore[arg-type]
        await asyncio.wait_for(controller.timeout_called.wait(), timeout=1)

        self.assertEqual(controller.operations, [(10, -20)])
        self.assertFalse(task.done())

        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(controller.disconnected_called)

    async def test_explicit_stop_does_not_start_timeout(self) -> None:
        controller = FakeController()
        server = OperationServer(controller)
        websocket = FakeWebSocket(
            [
                '{"leftMotorPwm": 10, "rightMotorPwm": -20}',
                '{"leftMotorPwm": 0, "rightMotorPwm": 0}',
            ]
        )

        task = asyncio.create_task(server.handle_connection(websocket))  # type: ignore[arg-type]
        while len(controller.operations) < 2:
            await asyncio.sleep(0)
        await asyncio.sleep(OPERATION_TIMEOUT_SECONDS + 0.1)

        self.assertEqual(controller.operations, [(10, -20), (0, 0)])
        self.assertFalse(controller.timeout_called.is_set())

        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

    async def test_debug_logs_every_received_message(self) -> None:
        controller = FakeController()
        server = OperationServer(controller)
        message = '{"leftMotorPwm": 10, "rightMotorPwm": -20}'
        websocket = FakeWebSocket([message])

        with self.assertLogs("server", level="DEBUG") as logs:
            task = asyncio.create_task(
                server.handle_connection(websocket)  # type: ignore[arg-type]
            )
            while not controller.operations:
                await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        self.assertTrue(
            any(
                f"Received operation message from {websocket.remote_address}: {message!r}"
                in entry
                for entry in logs.output
            )
        )


if __name__ == "__main__":
    unittest.main()
