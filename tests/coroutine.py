# vim:nowrap:textwidth=0

import unittest

from sheared.python import coroutine

class CoroutineTestCase(unittest.TestCase):
    def testReturn(self):
        """Test that return values propagate out of coroutines."""
        def f():
            return 42
        co = coroutine.Coroutine(f)
        self.assertRaises(coroutine.CoroutineReturned, co)
        self.assertEquals(co.result, 42, 'return-value is wrong')

    def testProducerConsumer(self):
        """Test producer-consumer coroutine pair."""
        list = []
        def writer(list):
            while 1:
                list.append(producer())
        def fib():
            f1, f2 = 0, 1
            while f1 < 100:
                f1, f2 = f2, f1 + f2
                consumer(f1)
        producer = coroutine.Coroutine(fib, 'fib')
        consumer = coroutine.Coroutine(writer, 'writer')
        try:
            self.assertRaises(coroutine.CoroutineReturned, consumer, list)
        except coroutine.CoroutineFailed, ex:
            exc_info = ex.args[0].exc_info
            raise exc_info[0], exc_info[1], exc_info[2]
        self.assertEqual(list, [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144])

    def testException(self):
        """Test that exceptions propagate out of coroutines."""
        def failer():
            assert 0
        co = coroutine.Coroutine(failer)
        try:
            co()
        except coroutine.CoroutineFailed, ex:
            self.assertEqual(co, ex.args[0], "propagated exception has wrong coroutine")
            self.assertEqual(co.exc_info[0], AssertionError, "propagated exception has wrong type")

suite = unittest.makeSuite(CoroutineTestCase, 'test')
