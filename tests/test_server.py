import unittest

from server import _parse_operation_message


class ParseOperationMessageTest(unittest.TestCase):
    def test_accepts_valid_pwm_values(self) -> None:
        self.assertEqual(_parse_operation_message('{"left": 10, "right": -20}'), (10, -20))

    def test_rejects_boolean_values(self) -> None:
        with self.assertRaises(ValueError):
            _parse_operation_message('{"left": true, "right": 0}')

    def test_rejects_out_of_range_values(self) -> None:
        with self.assertRaises(ValueError):
            _parse_operation_message('{"left": 256, "right": 0}')


if __name__ == "__main__":
    unittest.main()
