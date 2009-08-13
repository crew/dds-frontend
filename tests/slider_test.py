#!/usr/bin/env python
import clutter
import config
import slidemanager
from unittest import TestCase

CACHE = "./cache"

class SliderTest(TestCase):

  def setUp(self):
    self.slideshow = slidemanager.SlideManager(clutter.Stage())
    config.setOption("cache", CACHE)
    self.slideshow.addSlide({'id': 1, 'duration': 3,
                             'mode': 'layout', 'priority': 1,
                             'transition': 'fade'})
    self.slideshow.addSlide({'id': 2, 'duration': 3,
                             'mode': 'layout', 'priority': 1,
                             'transition': 'fade'})
    self.slideshow.addSlide({'id': 3, 'duration': 3,
                             'mode': 'layout', 'priority': 1,
                             'transition': 'fade'})
    self.slides = self.slideshow._slides

  def testSlideCommands(self):
    self.slideshow.removeSlide(1)
    self.slideshow.removeSlide(2)
    self.slideshow.removeSlide(3)
    self.assertTrue(slider.isEmpty(self.slides))
    self.slideshow.addSlide({'id': 1, 'duration': 3,
                          'mode': 'layout', 'priority': 1,
                          'transition': 'fade'})
    self.assertFalse(slider.isEmpty(self.slides))

  def testActivity(self):
    self.assertTrue(self.slideshow.isActive())
    self.slideshow.removeSlide(1)
    self.slideshow.removeSlide(2)
    self.slideshow.removeSlide(3)
    self.assertFalse(self.slideshow.isActive())
    self.slideshow.addSlide({'id': 3, 'duration': 3,
                          'mode': 'layout', 'priority': 1,
                          'transition': 'fade'})
    self.assertTrue(self.slideshow.isActive())

  def testSafeAddSlide(self):
    slide = clutter.Group()
    slide.id = 1
    self.assertFalse(slider.safeAddSlide(self.slides, slide))
    slide.id = 10
    self.assertTrue(slider.safeAddSlide(self.slides, slide))
