#!/usr/bin/env python
import random
import unittest

import xmppthread
import slideobject


class FakeConnection(object):
  
  def send(self, given):
    self.sentobj = given

class FakeSlideManager(object):

  def SetXMPPHandler(self, xmppt):
    self.xmpphandler = xmppt


class XMPPThreadTest(unittest.TestCase):

  def setUp(self):
    self.xt = xmppthread.XMPPThread()

  def tearDown(self):
    del self.xt

  def testsetCurrentSlide(self):
    self.xt.connection = FakeConnection()
    slide = slideobject.Slide()
    slide.id = random.randint(0, 1000)
    self.xt.SetCurrentSlide(slide)
    self.assertEqual(self.xt.connection.sentobj, self.xt.status)
    self.assertEqual(self.xt.status.getStatus(), 'Current=%s' % slide.id)

  def testattachSlideManager(self):
    sm = FakeSlideManager()
    self.xt.AttachSlideManager(sm)
    self.assertEqual(self.xt.slidemanager, sm)
    self.assertEqual(sm.xmpphandler, self.xt)
