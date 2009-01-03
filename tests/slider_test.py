#!/usr/bin/env python
import clutter
import config
from slider import Slider
from unittest import TestCase

CACHE = "./cache"

class SliderTest(TestCase):

  def setUp(self):
    self.slider = Slider(clutter.Stage())
    config.setOption("cache", CACHE)
    self.slider.addSlide(1, 3, 1)
    self.slider.addSlide(2, 3, 1)
    self.slider.addSlide(3, 3, 1)

  def testSlideCommands(self):
    self.slider.removeSlide(1)
    self.slider.removeSlide(2)
    self.slider.removeSlide(3)
    self.assertTrue(self.slider.isEmpty())
    self.slider.addSlide(1 ,1, 1)
    self.assertFalse(self.slider.isEmpty())

  def testActivity(self):
    self.assertTrue(self.slider.isActive())
    self.slider.removeSlide(1)
    self.slider.removeSlide(2)
    self.slider.removeSlide(3)
    self.assertFalse(self.slider.isActive())
    self.slider.addSlide(3, 3, 1)
    self.assertTrue(self.slider.isActive())
