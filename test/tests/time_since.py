import unittest
import time
from sheared.python.time_since import time_since
from sheared.python.time_since import strftime_since

class TimeSinceTestCase(unittest.TestCase):
    def testCrossover(self):
        """Test boundary conditions at cross over from one duration to
        the next greater (e.g. seconds -> minutes,seconds or
        minutes,seconds -> hours,minutes,seconds."""

        when = int(time.mktime((1979, 7, 7, 22, 0, 0, -1, -1, -1)))
        self.assertEquals(time_since(when, when),
                          (0, 0, 0, 0, 0, 0))

        # seconds/minutes cross over
        self.assertEquals(time_since(when, when + 59),
                          (0, 0, 0, 0, 0, 59))
        self.assertEquals(time_since(when, when + 60),
                          (0, 0, 0, 0, 1, 0))
        self.assertEquals(time_since(when, when + 61),
                          (0, 0, 0, 0, 1, 1))

        # minutes/hours cross over
        self.assertEquals(time_since(when, when + 59 * 60),
                          (0, 0, 0, 0, 59, 0))
        self.assertEquals(time_since(when, when + 59 + 59 * 60),
                          (0, 0, 0, 0, 59, 59))
        self.assertEquals(time_since(when, when + 60 * 60),
                          (0, 0, 0, 1, 0, 0))
        self.assertEquals(time_since(when, when + 1 + 60 * 60),
                          (0, 0, 0, 1, 0, 1))
        self.assertEquals(time_since(when, when + 61 * 60),
                          (0, 0, 0, 1, 1, 0))
        self.assertEquals(time_since(when, when + 1 + 61 * 60),
                          (0, 0, 0, 1, 1, 1))

        # The hours/days and days/months cross over conditions should
        # work, if the above does.

        # months/years
        self.assertEquals(time_since(when, when + 11 * 30 * 24 * 60 * 60),
                          (0, 11, 0, 0, 0, 0))
        self.assertEquals(time_since(when, when + 12 * 30 * 24 * 60 * 60 - 1),
                          (0, 11, 29, 23, 59, 59))
        self.assertEquals(time_since(when, when + 12 * 30 * 24 * 60 * 60),
                          (1, 0, 0, 0, 0, 0))
        self.assertEquals(time_since(when, when + 12 * 30 * 24 * 60 * 60 + 1),
                          (1, 0, 0, 0, 0, 1))

class StringFormatTimeSinceTestCase(unittest.TestCase):
    def testThing(self):
        self.assertEquals(strftime_since(0, 30),
                          "less than a minute")
        self.assertEquals(strftime_since(0, 60),
                          "1 minute")
        self.assertEquals(strftime_since(0, 90),
                          "1 minute")
        self.assertEquals(strftime_since(0, 120),
                          "2 minutes")

        self.assertEquals(strftime_since(0, 60 * 60),
                          "1 hour")
        self.assertEquals(strftime_since(0, 60 * 90),
                          "1 hour, 30 minutes")

        self.assertEquals(strftime_since(0, 5 * 24 * 60 * 60),
                          "5 days")
        self.assertEquals(strftime_since(0, 7 * 24 * 60 * 60),
                          "1 week")
        self.assertEquals(strftime_since(0, 9 * 24 * 60 * 60),
                          "1 week, 2 days")

        self.assertEquals(strftime_since(0, 30 * 24 * 60 * 60),
                          "1 month")
        self.assertEquals(strftime_since(0, 31 * 24 * 60 * 60),
                          "1 month, 1 day")
        self.assertEquals(strftime_since(0, 40 * 24 * 60 * 60),
                          "1 month, 10 days")

        self.assertEquals(strftime_since(0, 30 * 24 * 60 * 60, fields=2),
                          "1 month")
        self.assertEquals(strftime_since(0, 30 * 24 * 60 * 60 + 180, fields=2),
                          "1 month")
        self.assertEquals(strftime_since(0, 40 * 24 * 60 * 60, fields=2),
                          "1 month, 10 days")

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(TimeSinceTestCase, 'test')])
suite.addTests([unittest.makeSuite(StringFormatTimeSinceTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
