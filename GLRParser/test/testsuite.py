import unittest

suite = unittest.defaultTestLoader.discover(".","test_*.py")
unittest.TextTestRunner().run(suite)

