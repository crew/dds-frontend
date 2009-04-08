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

DEFAULTCONFIG = "~/.dds/config.py"
DEFAULTLOG = "~/.dds/log"

## Setup stupid logging for the client
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s', )

class DDS:
  def __init__(self):
    self._stage = clutter.stage_get_default()
    self._xmpp = None

  def parseArgs(self):
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("-c", "--config", dest="config", default=DEFAULTCONFIG,
                      metavar="FILE", help="set the config file to FILE")
    parser.add_option("-l", "--log", dest="log", default=DEFAULTLOG,
                      metavar="FILE", help="set the log file to FILE")
    parser.add_option("-n", "--nofull", dest="fullscreen", default=True,
                      help="No Fullscreen [For Debugging]",
                      action="store_false")
    parser.add_option("-b", "--letterbox", dest="letterbox", default=False,
                      action="store_true")
    parser.add_option("-t", "--notimers", dest="timersenabled", default=True,
                      help="No Timers [For Demos?]",
                      action="store_false")
    parser.add_option("-o", "--oneslide", dest="oneslide", default=None,
                      metavar="ID", type="int",
                      help="Display only one cached slideid")

    (options, args) = parser.parse_args()

    self._configfile = os.path.expanduser(options.config)
    self._logfile = os.path.expanduser(options.log)
    self._oneslide = options.oneslide
    self._letterbox = options.letterbox
    self._fullscreen = options.fullscreen
    self._timersenabled = options.timersenabled

  def onKeyPressEvent(self, stage, event):
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
    cache = config.option("cache")
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
    self._stage.connect('key-press-event', self.onKeyPressEvent)
    self._stage.hide_cursor()
    self._stage.set_title('CCIS Digital Display')
    self._stage.show_all()

  def pickRuntimeMode(self):
    ''' Decide to either: start XMPP or Display a single slide '''
    if not self._oneslide:
      self._xmpp = Xmpper(self._show)
      self._xmpp.start()
    else:
      try:
        slideid = int(self._oneslide)
      except:
        logging.error('Invalid integer passed for oneslide ID')
        sys.exit(1)
      slidedirectory = '%s/%s' % (config.option('cache'), slideid)
      if not os.path.exists(slidedirectory):
        logging.error('Could not display single slide id %s. Does %s exist?' %
                      (slideid, slidedirectory))
        sys.exit(1)
      self._show.addSlide(slideid, 100, 1)

  def main(self):
    self.initializeLibraries()
    self.parseArgs()
    config.init(self._configfile)
    self.setupCache()
    self.handleFullscreen()
    self.setupStage()
    self._show = Slider(self._stage, letterbox=self._letterbox,
                        timersenabled=self._timersenabled)
    self.pickRuntimeMode()
    clutter.main()

if __name__ == '__main__':
  d = DDS()
  d.main()
