import unittest
import sys
import io
from ._io import MemoryFormatIOBackend

class TestMemoryBackend(unittest.TestCase):
    def setUp(self):
        # Dummy fd/filename since MemoryBackend doesn't use them for storage
        self.backend = MemoryFormatIOBackend(fd=None, filename="test.part")

    def test_initial_state(self):
        self.assertEqual(len(self.backend), 0)
        self.assertFalse(self.backend.exists())

    def test_length_after_write(self):
        self.backend.initialize_writer()
        data = b"benchmark_data"
        self.backend.write(data)
        self.assertEqual(len(self.backend), len(data))
        self.assertTrue(self.backend.exists())

    def test_reset_behavior(self):
        self.backend.initialize_writer()
        self.backend.write(b"data")
        self.backend._reset()
        self.assertEqual(len(self.backend), 0)

if __name__ == '__main__':
    unittest.main()
