import importlib
import unittest


class SmokeImportTests(unittest.TestCase):
    def test_import_app(self) -> None:
        module = importlib.import_module("app")
        self.assertIsNotNone(module)


if __name__ == "__main__":
    unittest.main()
