#!/usr/bin/env python
import random
import unittest

import slideobject


class SlideObjectTest(unittest.TestCase):

  def setUp(self):
    self.sl = slideobject.Slide()

  def tearDown(self):
    del self.sl

  def testID(self):
    id = random.randint(0, 1000)
    self.sl.id = id
    self.assertEqual(id, self.sl.ID())

  def testSetParseDone(self):
    self.assertEqual(None, self.sl.parsedone)
    self.sl.SetParseDone(True)
    self.assertEqual(True, self.sl.parsedone)
    self.sl.SetParseDone(False)
    self.assertEqual(False, self.sl.parsedone)

if __name__ == '__main__':
    unittest.main()
