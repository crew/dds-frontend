#!/usr/bin/python

## This module tries importing everything, and bails if it didnt work.
import projectreqs
######################################################################
import clutter
import sys
import os
import config
import threading
import time
import gobject
import logging
from optparse import OptionParser
from slider import Slider
from xmpper import Xmpper

## Setup stupid logging for the client
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s', )

class DDS:
  def __init__(self):
    self._configFile = os.path.expanduser("~/.dds/config.py")
    self._logFile = os.path.expanduser("~/.dds/log")
    self._cache = None
    self._stage = clutter.stage_get_default()
    self._xmpp = None

  def parse_args(self):
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("-c", "--config", dest="config",
                      help="location of the config file")
    parser.add_option("-l", "--log", dest="log",
                      help="location of the log file")
    parser.add_option("-s", "--slides", dest="slides",
                      help=("location of the slide cache directory "
                            "(overides config file)"))
    parser.add_option("-n", "--nofull", dest="fullscreen", default=True,
                      help="No Fullscreen [For Debugging]",
                      action="store_false")
    parser.add_option("-b", "--letterbox", dest="letterbox", default=False,
                      action="store_true")
    parser.add_option("-t", "--notimers", dest="timersenabled", default=True,
                      help="No Timers [For Demos?]",
                      action="store_false")

    (options, args) = parser.parse_args()
    if (options.config):
      self._configFile = options.config
    if (options.log):
      self._logFile = options.log
    if (options.slides):
      self._cache = options.slides
    
    self._letterbox = options.letterbox
    self._fullscreen = options.fullscreen
    self._timersenabled = options.timersenabled

  def on_key_press_event(self, stage, event):
    logging.debug('Got keypress %s' % event.keyval)
    if (event.keyval == 113):
      clutter.main_quit()
      sys.exit(0)
    elif (event.keyval == 65363):
      if not self._timersenabled:
        logging.debug('Got arrow key, nexting?')
        self._show.next()
      else:
        logging.debug('Got arrow key, Will not advance without -t option')

  def setupStartupImage(self):
    ''' Create a black rectangle as a startup image. this should prevent the 
        ugly startup corruption we all know and love
    '''
    a = clutter.Rectangle()
    a.set_width(self._stage.get_width())
    a.set_height(self._stage.get_height())
    a.set_color(clutter.color_parse('black'))
    a.set_position(0,0)
    self._stage.add(a)

  def initializeLibraries(self):
    ''' Initialize the external libraries used '''
    gobject.threads_init()
    clutter.threads_init()
    # Fix a blocky text issue
    clutter.set_use_mipmapped_text(False)

  def setupCache(self):
    if (self._cache):
      config.setOption("cache", cache)
    cache = os.path.expanduser(config.option("cache"))
    if not os.path.exists(cache):
      os.makedirs(cache)

  def handleFullscreen(self):
    if self._fullscreen:
      logging.debug('Going Fullscreen')
      self._stage.fullscreen()

  def setupStage(self):
    self._stage.set_color(clutter.color_parse('black'))
    self.setupStartupImage()
    self._stage.connect('destroy', clutter.main_quit)
    self._stage.connect('key-press-event', self.on_key_press_event)
    self._stage.hide_cursor()
    self._stage.set_title('CCIS Digital Display')
    self._stage.show_all()

  def main(self, args):
    self.initializeLibraries()
    self.parse_args()
    config.init(self._configFile)
    self.setupCache()
    self.handleFullscreen()
    self.setupStage()
    self._show = Slider(self._stage, letterbox=self._letterbox,
                        timersenabled=self._timersenabled)
    self._xmpp = Xmpper(self._show)
    self._xmpp.start()
    clutter.main()

if __name__ == '__main__':
  d = DDS()
  retcode = d.main(sys.argv)
