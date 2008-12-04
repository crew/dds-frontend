#!/usr/bin/python
import config
import urllib
import os
import logging
from threading import Timer
from slideshow import Slideshow

class Slider(Slideshow):
  """Manages the order and timing of slide switching"""

  def __init__(self, canvas, letterbox=False):
    self.timer = None
    self.active = False
    Slideshow.__init__(self, canvas, letterbox=letterbox)

  def start(self):
    """Starts the Slider, should only be called when there are slides"""
    logging.debug('slider start')
    self.active = True
    self.setup_animation()
    self.reset_timer()
    self.paint()

  def stop(self):
    """Stops the Slideshow"""
    logging.debug('slider stop')
    self.active = False
    if self.timer:
      self.timer = None

  def reset_timer(self):
    """Runs the next timer thread to change slides"""
    logging.debug('slider reset_timer')

    if self.timer:
      self.timer = None

    if self.active:
      self.timer = Timer(float(self.currentSlide().duration),
                         self.next)
      self.timer.daemon = True
      self.timer.start()
      logging.debug('slider reset_timer new timer start')

  def next(self):
    """Runs the timer thread for, and shows the next slide"""
    logging.debug('slider next')
    Slideshow.next(self)
    self.reset_timer()
