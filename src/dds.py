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
    self._home = os.environ["HOME"]
    self._configFile = self._home + "/.dds/config.py"
    self._logFile = self._home + "/.dds/log"
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

  def on_key_press_event(self,stage, event):
    logging.debug('Got keypress %s' % event.keyval)
    if (event.keyval == 113):
      clutter.main_quit()
    elif (event.keyval == 65363):
      # In an ideal world, this would advance to the next slide
      # (right arrow key)
      if not self._timersenabled:
        logging.debug('Got arrow key, nexting?')
        self._show.next()
      else:
        logging.debug('Got arrow key, Will not advance without -t option')


  def main(self,args):
    logging.debug('Main method turn on!')
    gobject.threads_init()
    clutter.threads_init()
    clutter.set_use_mipmapped_text(False)
    self.parse_args()
    config.init(self._configFile)
    if (self._cache):
      config.setOption("cache", cache)
    cache = os.path.expanduser(config.option("cache"))
    if (not os.path.exists(cache)):
      os.makedirs(cache)
    logging.debug(os.path.exists(config.option("cache")))
    logging.debug(config.option("cache"))
    if self._fullscreen:
      logging.debug('Going Fullscreen')
      self._stage.fullscreen()
    self._stage.set_color(clutter.Color(0x00, 0x00, 0x00, 0x00))
    self._stage.connect('destroy', clutter.main_quit)
    self._stage.connect('key-press-event', self.on_key_press_event)
    self._stage.hide_cursor()
    self._stage.show_all()
    logging.debug('Creating slider')
    self._show = Slider(self._stage, letterbox=self._letterbox,
                        timersenabled=self._timersenabled)
    logging.debug('Creating xmpper')
    self._xmpp = Xmpper(self._show)
    logging.debug('Starting xmpper')
    self._xmpp.start()
    logging.debug('Clutter Main invocation')
    clutter.main()



if __name__ == '__main__':
  d = DDS()
  retcode = d.main(sys.argv)
  print retcode
  sys.exit(retcode)
