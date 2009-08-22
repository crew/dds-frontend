#!/usr/bin/env python
import clutter
import config
import mox
import unittest

import slidemanager
import slideobject

CACHE = "./cache"


class SlideManagerTest(unittest.TestCase):

  def setUp(self):
    self.sm = slidemanager.SlideManager(None)
    self.mox = mox.Mox()

  def tearDown(self):
    del self.sm
    del self.mox

  def testisActive(self):
    self.sm._active = False
    self.assertEqual(False, self.sm.isActive())
    self.sm._active = True
    self.assertEqual(True, self.sm.isActive())

  def testhasMultipleSlides(self):
    # Should be empty here
    self.assertEqual(False, self.sm.hasMultipleSlides())
    
    # Add an object to the slide list (one slide)
    self.sm._slides.append(object())
    self.assertEqual(False, self.sm.hasMultipleSlides())

    # Add an object to the slide list (two slides)
    self.sm._slides.append(object())
    self.assertEqual(True, self.sm.hasMultipleSlides())

  def teststop(self):
    self.sm._active = True
    self.assertEqual(True, self.sm.isActive())
    self.sm.stop()
    self.assertEqual(False, self.sm.isActive())
  
  def testlogSlideOrder(self):
    s1 = slideobject.Slide()
    s1.id = 1
    s2 = slideobject.Slide()
    s2.id = 2
    self.sm._slides = [s1, s2]
    emsg = 'Current Slide Order: [1, 2]'
    self.assertEqual(emsg, self.sm.logSlideOrder())

  def testisEmpty(self):
    # Should be empty here
    self.assertEqual(True, self.sm.isEmpty())
    
    # Add an object to the slide list
    self.sm._slides.append(object())
    self.assertEqual(False, self.sm.isEmpty())

  def testcurrentSlide(self):
    s1 = slideobject.Slide()
    s1.id = 1
    s2 = slideobject.Slide()
    s2.id = 2
    self.sm._slides = [s1, s2]
    self.assertEqual(s1, self.sm.currentSlide())

  def testupdateSlide(self):
    testslidetuple = object()

    mockslide1 = mox.MockObject(slideobject.Slide)
    mockslide2 = mox.MockObject(slideobject.Slide)
    self.sm._slides = [mockslide1, mockslide2]

    mockslide1.canUpdateManifest(testslidetuple).AndReturn(False)
    mockslide2.canUpdateManifest(testslidetuple).AndReturn(True)

    mockslide2.ID().AndReturn(2)

    mockslide2.updateManifest(testslidetuple)

    mox.Replay(mockslide1)
    mox.Replay(mockslide2)

    self.sm.updateSlide(testslidetuple)

    mox.Verify(mockslide1)
    mox.Verify(mockslide2)

if __name__ == '__main__':
    unittest.main()
