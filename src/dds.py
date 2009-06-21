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
import xmpper
from optparse import OptionParser
from slider import Slider

DEFAULTCONFIG = "~/.dds/config.py"
DEFAULTLOG = "~/.dds/log"

def parseArgs():
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

  configfile = os.path.expanduser(options.config)
  logfile = os.path.expanduser(options.log)
  oneslide = options.oneslide
  letterbox = options.letterbox
  fullscreen = options.fullscreen
  timersenabled = options.timersenabled
  return (configfile, logfile, oneslide, letterbox, fullscreen, timersenabled)

def onKeyPressEvent(stage, event, show, timersenabled):
  logging.debug('Got keypress %s' % event.keyval)
  if (event.keyval == 113):
    clutter.main_quit()
    sys.exit(0)
  elif (event.keyval == 65363):
    if not timersenabled:
      logging.debug('Got arrow key, nexting?')
      show.next()
    else:
      logging.debug('Got arrow key, Will not advance without -t option')

def setupStartupImage(stage):
  '''Create a black rectangle as a startup image. This should prevent the
  ugly startup corruption we all know and love.
  '''
  a = clutter.Rectangle()
  a.set_width(stage.get_width())
  a.set_height(stage.get_height())
  a.set_color(clutter.color_parse('black'))
  a.set_position(0,0)
  stage.add(a)

def initializeLibraries():
  '''Initialize the external libraries used.'''
  gobject.threads_init()
  clutter.threads_init()
  # Fix a blocky text issue
  clutter.set_use_mipmapped_text(False)

def setupCache():
  cache = config.option("cache")
  if not os.path.exists(cache):
    os.makedirs(cache)

def handleFullscreen(stage, fullscreen):
  if fullscreen:
    logging.debug('Going Fullscreen')
    stage.fullscreen()

def setupStage(stage, show, timersenabled, fullscreen):
  handleFullscreen(stage, fullscreen)
  stage.set_color(clutter.color_parse('black'))
  setupStartupImage(stage)
  stage.connect('destroy', clutter.main_quit)
  stage.connect('key-press-event', onKeyPressEvent, show, timersenabled)
  stage.hide_cursor()
  stage.set_title('CCIS Digital Display')
  stage.show_all()

def pickRuntimeMode(show, oneslide):
  '''Decide to either: start XMPP or display a single slide.'''
  if not oneslide:
    xmpper.start(show)
  else:
    try:
      slideid = int(oneslide)
    except:
      logging.error('Invalid integer passed for oneslide ID')
      sys.exit(1)

    slidedirectory = '%s/%s' % (config.option('cache'), slideid)
    if not os.path.exists(slidedirectory):
      logging.error('Could not display single slide id %s. Does %s exist?' %
                    (slideid, slidedirectory))
      sys.exit(1)
    show.addSlide(slideid, 100, 1)

def main():
  initializeLibraries()
  logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s %(levelname)s %(message)s')
  stage = clutter.stage_get_default()
  (configfile, logfile, oneslide, letterbox, fullscreen, timersenabled) = parseArgs()
  config.init(configfile)
  setupCache()
  show = Slider(stage, letterbox, timersenabled)
  setupStage(stage, show, timersenabled, fullscreen)
  pickRuntimeMode(show, oneslide)
  clutter.main()

if __name__ == '__main__':
  main()
