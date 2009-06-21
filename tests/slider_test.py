#!/usr/bin/env python
import clutter
import config
import slider
from unittest import TestCase

CACHE = "./cache"

class SliderTest(TestCase):

  def setUp(self):
    self.slider = slider.Slider(clutter.Stage())
    config.setOption("cache", CACHE)
    self.slider.addSlide({'id': 1, 'duration': 3,
                          'mode': 'layout', 'priority': 1,
                          'transition': 'fade'})
    self.slider.addSlide({'id': 2, 'duration': 3,
                          'mode': 'layout', 'priority': 1,
                          'transition': 'fade'})
    self.slider.addSlide({'id': 3, 'duration': 3,
                          'mode': 'layout', 'priority': 1,
                          'transition': 'fade'})

  def testSlideCommands(self):
    self.slider.removeSlide(1)
    self.slider.removeSlide(2)
    self.slider.removeSlide(3)
    self.assertTrue(slider.isEmpty(self.slider._slides))
    self.slider.addSlide({'id': 1, 'duration': 3,
                          'mode': 'layout', 'priority': 1,
                          'transition': 'fade'})
    self.assertFalse(slider.isEmpty(self.slider._slides))

  def testActivity(self):
    self.assertTrue(self.slider.isActive())
    self.slider.removeSlide(1)
    self.slider.removeSlide(2)
    self.slider.removeSlide(3)
    self.assertFalse(self.slider.isActive())
    self.slider.addSlide({'id': 3, 'duration': 3,
                          'mode': 'layout', 'priority': 1,
                          'transition': 'fade'})
    self.assertTrue(self.slider.isActive())
