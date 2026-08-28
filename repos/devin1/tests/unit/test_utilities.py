import unittest
from utilities.common import calculate_sum, format_string, is_valid_email

class TestUtilities(unittest.TestCase):
    def test_calculate_sum(self):
        # Test with positive integers
        self.assertEqual(calculate_sum(10, 5), 15)
        # Test with negative integers
        self.assertEqual(calculate_sum(-10, -5), -15)
        # Test with mixed integers
        self.assertEqual(calculate_sum(-10, 10), 0)

    def test_format_string(self):
        # Test with a standard string
        self.assertEqual(format_string("  hello world  "), "Hello World")
        # Test with numbers in the string
        self.assertEqual(format_string("  python 101  "), "Python 101")
        # Test with an empty string
        self.assertEqual(format_string(""), "")

    def test_is_valid_email(self):
        # Test with valid email
        self.assertTrue(is_valid_email("test@example.com"))
        # Test with invalid email
        self.assertFalse(is_valid_email("invalid-email"))
        # Test with edge cases
        self.assertFalse(is_valid_email("@example.com"))
        self.assertFalse(is_valid_email("test@.com"))

if __name__ == "__main__":
    unittest.main()
