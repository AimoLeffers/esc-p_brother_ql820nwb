import unittest
from main import mm_to_dots
from main import dots_to_hex
from main import get_parity_byte


class MmToDotsTests(unittest.TestCase):
    def test_positve_floats(self):
        self.assertEqual(mm_to_dots(50.8), 600)
        self.assertEqual(mm_to_dots(25.4), 300)
        self.assertEqual(mm_to_dots(10.0), 118)
        self.assertEqual(mm_to_dots(1.0), 12)

    def test_positive_ints(self):
        self.assertRaises(ValueError, mm_to_dots, 2)

    def test_negative_values(self):
        self.assertRaises(ValueError, mm_to_dots, -50.8)


class DotsToHexTests(unittest.TestCase):
    def test_positive_values(self):
        self.assertEqual(dots_to_hex(600), (b"\x58", b"\x02"))
        self.assertEqual(dots_to_hex(50), (b"\x32", b"\x00"))
        self.assertEqual(dots_to_hex(8000), (b"\x40", b"\x1F"))
        self.assertRaises(ValueError, dots_to_hex, 8001)

    def test_negative_values(self):
        self.assertRaises(ValueError, dots_to_hex, -5)


class GetParityByteTests(unittest.TestCase):
    def test_string_values(self):
        self.assertEqual(get_parity_byte('1234'), b'\x04')
        self.assertEqual(get_parity_byte('123456789'), b'\x31')


if __name__ == '__main__':
    unittest.main()
