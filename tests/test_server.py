import asyncio
import unittest

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

    def __init__(self) -> None:
        self.receive_count = 0

    async def recv(self) -> str:
        self.receive_count += 1
        if self.receive_count == 1:
            return '{"left": 10, "right": -20}'

        await asyncio.Event().wait()
        raise AssertionError("unreachable")


class ParseOperationMessageTest(unittest.TestCase):
    def test_accepts_valid_pwm_values(self) -> None:
        self.assertEqual(_parse_operation_message('{"left": 10, "right": -20}'), (10, -20))

    def test_rejects_boolean_values(self) -> None:
        with self.assertRaises(ValueError):
            _parse_operation_message('{"left": true, "right": 0}')

    def test_rejects_out_of_range_values(self) -> None:
        with self.assertRaises(ValueError):
            _parse_operation_message('{"left": 256, "right": 0}')


class OperationServerTest(unittest.IsolatedAsyncioTestCase):
    async def test_operation_timeout_is_handled_without_escaping(self) -> None:
        controller = FakeController()
        server = OperationServer(controller)
        websocket = FakeWebSocket()

        task = asyncio.create_task(server.handle_connection(websocket))  # type: ignore[arg-type]
        await asyncio.wait_for(controller.timeout_called.wait(), timeout=1)

        self.assertEqual(controller.operations, [(10, -20)])
        self.assertFalse(task.done())

        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(controller.disconnected_called)


if __name__ == "__main__":
    unittest.main()
