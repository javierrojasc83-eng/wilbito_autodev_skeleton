import unittest

from artifacts.codegen.calc import sumar


class TestCalc(unittest.TestCase):
    def test_sumar_basico(self):
        self.assertEqual(sumar(2, 3), 5)


if __name__ == "__main__":
    unittest.main()
