#!/usr/bin/env python
import mox
import unittest

import config


class ConfigTest(unittest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()

  def tearDown(self):
    del self.mox

  def testFIXME(self):
    self.assert_(True)
