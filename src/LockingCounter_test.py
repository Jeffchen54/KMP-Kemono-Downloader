import time
import unittest
from LockingCounter import LockingCounter
import threading

class LockingCounterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """
        Create counter starting at 0
        """
        self.counter = LockingCounter()
        
    def test_wait_for(self) -> None:
        """
        Tests a single wait_for cycle
        """
        # Generate a thread
        t1 = threading.Thread(target=self.wait_thread, args=(5,))
        t1.start()
        # Keep incrementing until target is met
        self.counter.toggle()
        self.assertTrue(t1.is_alive())
        self.counter.toggle()
        self.assertTrue(t1.is_alive())
        self.counter.toggle()
        self.assertTrue(t1.is_alive())
        self.counter.toggle()
        self.assertTrue(t1.is_alive())
        self.counter.toggle()
        time.sleep(0.1)
        self.assertFalse(t1.is_alive())

        # Generate another thread when target is met
        t1 = threading.Thread(target=self.wait_thread, args=(5,))
        self.assertFalse(t1.is_alive())
        t1 = threading.Thread(target=self.wait_thread, args=(0,))
        self.assertFalse(t1.is_alive())
    def wait_thread(self, target:int)->None:
        """
        Wait until target is met, to be used with threading

        Args:
            target (int): target to wait for
        """
        self.counter.wait_until(target)

if __name__ == '__main__':
    unittest.main()