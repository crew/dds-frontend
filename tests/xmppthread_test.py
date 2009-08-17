#!/usr/bin/env python
import mox
import unittest

import xmppthread


class XMPPThreadTest(unittest.TestCase):

  def setUp(self):
    self.xt = xmppthread.XMPPThread()
    self.mox = mox.Mox()

  def tearDown(self):
    del self.xt
    del self.mox

  def testFIXME(self):
    self.assert_(True)
