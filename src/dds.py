#!/usr/bin/python

## This module tries importing everything, and bails if it didnt work.
import projectreqs
######################################################################
import clutter
import config
import gflags as flags
import gobject
import logging
import os
import sys
import threading
import time
import xmpper
from slider import Slider

flags.DEFINE_boolean('fullscreen', True, 'Control fullscreen behavior')
flags.DEFINE_boolean('enabletimers', True,
                     'Control automatic slide advancement')
flags.DEFINE_integer('oneslide', 0, 'Display only the given slide ID')
flags.DEFINE_string('logfile', '~/.dds/log', 'Log file path')

FLAGS = flags.FLAGS


def onKeyPressEvent(stage, event, show):
  logging.debug('Got keypress %s' % event.keyval)
  if (event.keyval == 113):
    clutter.main_quit()
    sys.exit(0)
  elif (event.keyval == 65363):
    if not FLAGS.enabletimers:
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

def handleFullscreen(stage):
  if FLAGS.fullscreen:
    logging.debug('Going Fullscreen')
    stage.fullscreen()

def setupStage(stage, show):
  handleFullscreen(stage)
  stage.set_color(clutter.color_parse('black'))
  setupStartupImage(stage)
  stage.connect('destroy', clutter.main_quit)
  stage.connect('key-press-event', onKeyPressEvent, show)
  stage.hide_cursor()
  stage.set_title('CCIS Digital Display')
  stage.show_all()

def pickRuntimeMode(show):
  '''Decide to either: start XMPP or display a single slide.'''
  if not FLAGS.oneslide:
    xmpper.start(show)
  else:
    try:
      slideid = int(FLAGS.oneslide)
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
  config.init()
  setupCache()
  show = Slider(stage)
  setupStage(stage, show)
  pickRuntimeMode(show)
  clutter.main()

if __name__ == '__main__':
  FLAGS(sys.argv)
  main()
