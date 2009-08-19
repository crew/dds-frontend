import config
import glob
import urllib
import time
import os.path
import logging

from threading import Timer
import xml.sax as sax
from xml.sax.handler import ContentHandler
from xml.sax.handler import ErrorHandler

from slideshow import Slideshow

class Slider(Slideshow):
  """Manages the order and timing of slide switching"""

  def __init__(self, canvas):
    self.timer = None
    self.active = False
    Slideshow.__init__(self, canvas)

  def start(self):
    """Starts the Slider, should only be called when there are slides"""

    self.active = True
    self.setup_animation()
    self.reset_timer()
    self.paint()

  def stop(self):
    """Stops the Slideshow"""

    logging.debug('stopping slider')

    self.active = False
    if self.timer:
      self.timer = None

  def reset_timer(self):
    """Runs the next timer thread to change slides"""

    if self.timer:
      self.timer = None

    if self.active:
      self.timer = Timer(float(self.currentSlide().duration),
                         self.next)
      self.timer.daemon = True
      self.timer.start()

  def next(self):
    """Runs the timer thread for, and shows the next slide"""

    Slideshow.next(self)
    self.reset_timer()
