#!/usr/bin/python
"""CCIS Crew Digital Display System Frontend/Client

This module is the executable for the DDS Client, all signs will run this in a
X SESSION to display pretty slides to users around the world.
"""

__author__ = 'CCIS Crew <crew@ccs.neu.edu>'


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
flags.DEFINE_string('logfile', '~/.dds/log', 'Log file path')
flags.DEFINE_string('userdir', '~/.dds', 'user state path')

FLAGS = flags.FLAGS


def createDDSDir():
  """Create the user's DDS dir if it does not exist."""
  DIR = os.path.expanduser(FLAGS.userdir)
  if not os.path.exists(DIR):
    os.makedirs(DIR)

def onKeyPressEvent(stage, event, show):
  """Handle Keypress Events.

  Args:
     event: (clutter event) keypress event
     show: (Slider) Slideshow instance
  """
  logging.debug('Got keypress %s' % event.keyval)
  if (event.keyval == 113):
    clutter.main_quit()
    sys.exit(0)
  elif (event.keyval == 65363):
    if not FLAGS.enabletimers:
      logging.debug('Got arrow key, nexting?')
      show.next()
    else:
      logging.debug('Got arrow key, Will not advance without disabling timers')

def setupStartupImage(stage):
  """Setup the Startup Screen.

  Args:
     stage: (Clutter Stage)

  Create a black rectangle as a startup image. This should prevent the
  ugly startup corruption we all know and love.
  """
  a = clutter.Rectangle()
  a.set_width(stage.get_width())
  a.set_height(stage.get_height())
  a.set_color(clutter.color_parse('black'))
  a.set_position(0,0)
  stage.add(a)

def initializeLibraries():
  """Initialize the external libraries used."""
  gobject.threads_init()
  clutter.threads_init()
  # Fix a blocky text issue
  clutter.set_use_mipmapped_text(False)

def setupCache():
  """Create cache directory if it does not exist."""
  cache = config.option("cache")
  if not os.path.exists(cache):
    os.makedirs(cache)

def handleFullscreen(stage):
  """Setup fullscreen mode if enabled.

  Args:
     stage: (Clutter Stage)
  """
  if FLAGS.fullscreen:
    logging.debug('Going Fullscreen')
    stage.fullscreen()

def setupStage(stage, show):
  """Setup the Clutter Stage.

  Args:
     stage: (Clutter Stage)
     show: (Slider) Slideshow instance
  """
  handleFullscreen(stage)
  stage.set_color(clutter.color_parse('black'))
  setupStartupImage(stage)
  stage.connect('destroy', clutter.main_quit)
  stage.connect('key-press-event', onKeyPressEvent, show)
  stage.hide_cursor()
  stage.set_title('CCIS Digital Display')
  stage.show_all()

def main():
  """Initiate a DDS frontend."""
  createDDSDir()
  initializeLibraries()
  logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s %(levelname)s %(message)s')
  stage = clutter.stage_get_default()
  config.init()
  setupCache()
  show = Slider(stage)
  setupStage(stage, show)
  xmpper.start(show)
  clutter.main()

if __name__ == '__main__':
  FLAGS(sys.argv)
  main()
