#!/usr/bin/python
import config
import urllib
import os
import logging
import gobject
from slideshow import Slideshow

class Slider(Slideshow):
  """Manages the order and timing of slide switching"""

  def __init__(self, canvas, letterbox=False):
    self.active = False
    self.scheduled_timer = False
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

  def reset_timer(self):
    """Runs the next timer thread to change slides"""
    logging.debug('slider reset_timer')
    
    if self.currentSlide() is not None and not self.scheduled_timer:
      self.scheduled_timer = True
      gobject.timeout_add(1000*self.currentSlide().duration, self.next)
    elif self.scheduled_timer:
      logging.debug('Cannot schedule, already scheduled')

  def next(self):
    """Runs the timer thread for, and shows the next slide"""
    logging.debug('slider next')
    if self.isEmpty() or not self.active:
      # We don't have any slides, there is nothing to do!
      return False
    self.scheduled_timer = False
    Slideshow.next(self)
    self.reset_timer()
    return False
