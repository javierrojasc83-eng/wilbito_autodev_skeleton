import unittest

from artifacts.codegen.demo import demo


class TestDemo(unittest.TestCase):
    def test_demo(self):
        self.assertEqual(demo(), "ok")


if __name__ == "__main__":
    unittest.main()
