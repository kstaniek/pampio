"""Test CRC function."""


from unittest import TestCase
from pampio.utils import calc_crc


class TestCRC(TestCase):
    def test_crc(self):
        data = b'\x00\x00\x00\x00\x0f\x00\x00\x00\x08\x00\x00\x13\x05\x0d\x00\x04\x00'
        self.assertEqual(calc_crc(data), 0x6d)
