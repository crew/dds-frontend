#!/usr/bin/env python
import unittest

import xmppthread


class XMPPThreadTest(unittest.TestCase):

  def setUp(self):
    self.xt = xmppthread.XMPPThread()

  def tearDown(self):
    del self.xt

  def testFIXME(self):
    self.assert_(True)
