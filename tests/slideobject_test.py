#!/usr/bin/env python
import mox
import unittest

import slideobject


class SlideObjectTest(unittest.TestCase):

  def setUp(self):
    self.sl = slideobject.Slide()
    self.mox = mox.Mox()

  def tearDown(self):
    del self.sl
    del self.mox

  def testID(self):
    self.sl.id = 45
    self.assertEqual(45, self.sl.ID())

  def testsetParseDone(self):
    self.assertEqual(None, self.sl.parsedone)
    self.sl.setParseDone(True)
    self.assertEqual(True, self.sl.parsedone)
    self.sl.setParseDone(False)
    self.assertEqual(False, self.sl.parsedone)

