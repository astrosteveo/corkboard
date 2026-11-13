import unittest

import corkboard


class PackageTest(unittest.TestCase):
    def test_package_imports(self):
        self.assertIn("standard library", corkboard.__doc__)


if __name__ == "__main__":
    unittest.main()
