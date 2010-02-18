#!/usr/bin/python
"""CCIS Crew Digital Display System Frontend/Client

This module is the executable for the DDS Client, all signs will run this in a
X SESSION to display pretty slides to users around the world.
"""

__author__ = 'CCIS Crew <crew@ccs.neu.edu>'


import clutter
import cairo
import config
import gflags
import gobject
import logging
import os
import sys
import threading

## DDS Imports
import xmppthread
import manager
import slideobject

gflags.DEFINE_boolean('fullscreen', True, 'Control fullscreen behavior')
gflags.DEFINE_boolean('debug', False, 'Enable debug logging')
gflags.DEFINE_string('logfile', '~/.dds/log', 'Log file path')
gflags.DEFINE_string('userdir', '~/.dds', 'user state path')
gflags.DEFINE_boolean('enablemanualadvance', False,
                     'Controls manual slide advancement')
gflags.DEFINE_string('oneslide', None, 'Display only the given slidedir')
gflags.DEFINE_integer('height', 540, 'Windowed Height')
gflags.DEFINE_integer('width', 960, 'Windowed Width')

FLAGS = gflags.FLAGS

# Global variable to track fullscreen state
FULLSCREEN = False


def CreateDDSDir():
  """Create the user's DDS dir if it does not exist."""
  directory = os.path.expanduser(FLAGS.userdir)
  if not os.path.exists(directory):
    os.makedirs(directory)

def OnKeyPressEvent(stage, event, show):
  """Handle Keypress Events.

  Args:
     event: (clutter event) keypress event
     show: (Slider) Slideshow instance
  """
  logging.debug('Got keypress %s' % event.keyval)
  # Handle `q`
  if (event.keyval == 113):
    clutter.main_quit()
    sys.exit(0)
  elif (event.keyval == 65363):
    if FLAGS.enablemanualadvance:
      logging.debug('Got arrow key, nexting?')
      show.next()
    else:
      logging.debug('Got arrow key, manual advance disabled')


def SetupStartupImage(stage):
  """Setup the Startup Screen.

  Args:
     stage: (Clutter Stage)

  Create a black rectangle as a startup image. This should prevent the
  ugly startup corruption we all know and love.
  """
  background = clutter.Rectangle()
  background.set_width(stage.get_width())
  background.set_height(stage.get_height())
  background.set_color(clutter.color_from_string('black'))
  background.set_position(0, 0)
  stage.add(background)


def InitializeLibraries():
  """Initialize the external libraries used."""
  gobject.threads_init()
  #FIXME This is sort of a hack. We force all clutter clients to use the same
  # resolution so things look the same across all clients.
  clutter.Backend.set_resolution(clutter.backend_get_default(), 112)

  # Make the font rendering look a little nicer
  font_options = clutter.Backend.get_font_options(clutter.backend_get_default())
  font_options.set_hint_style(cairo.HINT_STYLE_NONE);
  font_options.set_antialias(cairo.ANTIALIAS_SUBPIXEL);
  clutter.Backend.set_font_options(clutter.backend_get_default(), font_options);

def SetupCache():
  """Create cache directory if it does not exist."""
  cache = config.Option("cache")
  if not os.path.exists(cache):
    os.makedirs(cache)


def HandleFullscreen(stage):
  """Setup fullscreen mode if enabled.

  Args:
     stage: (Clutter Stage)
  """
  global FULLSCREEN
  if FLAGS.fullscreen:
    logging.debug('Going Fullscreen')
    FULLSCREEN = True
    stage.set_fullscreen(True)
  else:
    stage.set_height(FLAGS.height)
    stage.set_width(FLAGS.width)
    stage.set_fullscreen(False)


def SetupStage(stage, show):
  """Setup the Clutter Stage.

  Args:
     stage: (Clutter Stage)
     show: (Slider) Slideshow instance
  """
  stage.set_color(clutter.color_from_string('black'))
  SetupStartupImage(stage)
  stage.hide_cursor()
  stage.connect('destroy', clutter.main_quit)
  stage.connect('key-press-event', OnKeyPressEvent, show)
  stage.set_title('CCIS Digital Display')
  stage.show_all()


def Main():
  """Initiate a DDS frontend."""
  CreateDDSDir()
  InitializeLibraries()
  level = logging.INFO
  if FLAGS.debug:
    level = logging.DEBUG
  logging.basicConfig(level=level,
                      format='%(asctime)s %(filename)s %(lineno)d '
                             '%(levelname)s %(message)s')
  stage = clutter.Stage()
  HandleFullscreen(stage)
  SetupCache()
  show = manager.Manager(stage)
  SetupStage(stage, show)
  if not FLAGS.oneslide:
    timer = xmppthread.XMPPThread()
    timer.AttachSlideManager(show)
    timer.start()
  else:
    def foo():
      show.slides.playlist.add({'position':1, 'mode':'single', 'slides':[-1],
                                'weights':[1]})
      show.slides.playlist.add({'position':1, 'mode':'single', 'slides':[-2],
                                'weights':[1]})
      s = slideobject.Slide()
      s.oneslide(FLAGS.oneslide)
      a = slideobject.Slide()
      a.oneslide(FLAGS.oneslide, id=-2)
      show._add_slide(s)
      show._add_slide(a)
    t = threading.Thread(target=foo)
    t.start()

  clutter.main()

if __name__ == '__main__':
  FLAGS(sys.argv)
  Main()
