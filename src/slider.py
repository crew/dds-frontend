#!/usr/bin/python
import clutter
from clutter import Script
import config
import gflags as flags
import gobject
import hashlib
import imp
import logging
import os
import sys

flags.DEFINE_integer('lheight', 12, 'L_HEIGHT Constant')
flags.DEFINE_integer('wheight', 9, 'W_HEIGHT Constant')
flags.DEFINE_boolean('letterbox', False,
                     'Set the view mode to use letterboxing')
flags.DEFINE_boolean('enabletimers', True,
                     'Control automatic slide advancement')

FLAGS = flags.FLAGS

class Slider(object):
  """Handles the painting and parsing of slides"""

  def __init__(self, stage):
    self._stage = stage
    self._current = None
    self._last = None
    self._paintran = False
    self._timer_scheduled = False
    self._active = False
    self._slides = []

  def addSlide(self, info):
    """Add a new slide to the internal cache.

    Args:
       info: (dictionary) new slide information
    Returns:
       False on add failure (for unsupported or improperly parsed slides)
    """
    directory = "%s/%s" % (config.option("cache"), str(info["id"]))
    if "layout" == info["mode"]:
      layoutfile = '%s/%s' % (directory, 'layout.js')
      slide = parseLayout(layoutfile, directory, self._stage)

    elif "module" == info["mode"]:
      pythonfile = '%s/%s' % (directory, 'layout.py')
      slide = parsePython(pythonfile, directory, self._stage)
      if not slide:
        return False

    elif "executable" == info["mode"]:
      logging.error('Executable slide types not supported, skipping')
      return False

    else:
      logging.error('Unknown slide type "%s" given, skipping' % info['mode'])
      return False

    slide.id = info["id"]
    slide.duration = info["duration"]
    slide.priority = info["priority"]
    slide.transition = info["transition"]
    empty = isEmpty(self._slides)
    safeAddSlide(self._slides, slide)
    if empty:
      self._current = currentSlide(self._slides)
      self.start()
    return False

  def removeSlide(self, removalid):
    """Remove the slide with the given id from the cache

    Args:
       removalid: (int) Slide ID to remove
    """
    if removalid not in map(lambda x: x.id, self._slides):
      logging.debug(('I was told to remove slide id %s from the deck, but its'
                     ' already gone') % removalid)
    else:
      logging.debug('I was told to remove slide id %s from the deck'
                    % removalid)
    logSlideOrder(self._slides)
    for slide in self._slides:
      if slide.id == removalid:
        logging.info('Removing slide %s from the deck' % removalid)
        self._slides.remove(slide)
        logSlideOrder(self._slides)
    if isEmpty(self._slides):
      self.stop()

  def next(self):
    """Runs the timer thread for, and shows the next slide"""
    logging.debug('slider next')
    self._timer_scheduled = False
    if not isEmpty(self._slides) and self.isActive():
      if self._last is None:
        self._last = self._current

      self._current, self._last = loadNextAndPaint(self._current, self._last,
                                                   self._stage, self._slides)

      createNextTimer(self.next, self._current)
    return False

  def start(self):
    """
    Starts the slider. This should only be called when there are slides
    and if the slider isn't already active.
    """
    logging.debug('slider start')
    if self.isActive():
      logging.error("Attempted to start an already active slider.")
    elif isEmpty(self._slides):
      logging.error("Attempted to start an empty slider.")
    else:
        self._active = True
        setupAnimation(self._current, self._stage)
        createNextTimer(self.next, currentSlide(self._slides))
        paint(self._current, self._stage)

  def stop(self):
    """Stops the Slideshow"""
    logging.debug('slider stop')
    self._active = False

  def isActive(self):
    """Determines if this slider's active."""
    return self._active

def parseLayout(filename, directory, stage):
  """Parses the given json file into a slide.

  Args:
     filename: (string) json filename
     directory: (string) json directory
     stage: (Clutter Stage) stage to draw layout on

  Returns:
     Parsed slide from setupNewSlide
  """
  logging.debug('Parsing layout filename: %s dir: %s' % (filename, directory))
  script = Script()
  script.add_search_paths(directory)
  script.load_from_file(filename)
  slide = script.get_object('slide')
  return setupNewSlide(slide, stage)

def parsePython(filename, directory, stage):
  """Returns a slide from the given python module.

  Args:
     filename: (string) python module filename
     directory: (string) python module directory
     stage: (Clutter Stage) stage to draw layout on

  Returns:
     Parsed slide from setupNewSlide
  """
  try:
    slideModule = loadModule(filename, directory)
    return setupNewSlide(slideModule.slide, stage)
  except Exception, e:
    logging.error('Could not load module %s in dir %s because %s'
                  % (filename, directory, e))

def setupNewSlide(slide, stage):
  """Sets the correct height and width for the given freshly parsed slide.

  Args:
     slide: (Clutter Slide)
     stage: (Clutter Stage)

  Returns:
     Clutter Slide
  """
  for child in slide.get_children():
    if (FLAGS.letterbox):
      letterbox_y = (stage.get_height() / FLAGS.lheight) * 1.5
      height_div = FLAGS.lheight
    else:
      letterbox_y = 0
      height_div = FLAGS.wheight
    child.set_x(child.get_x() * (stage.get_width() / 16))
    child.set_y(letterbox_y + child.get_y() * (stage.get_height() /
                                               height_div))
    child.set_width(child.get_width() * (stage.get_width() / 16))
    child.set_height(child.get_height() * (stage.get_height() /
                                           height_div))
  return slide

def loadModule(codepath, directory):
  """Returns the module object for the python file at the given path.

  Args:
     codepath: (string) filename to load
     directory: (string) directory that filename resides in
  """
  fin = None
  try:
    currentDirectory = os.getcwd()
    currentPath = sys.path
    sys.path.append(directory)
    os.chdir(directory)
    fin = open(codepath, 'rb')
    module = imp.load_source(hashlib.sha1(codepath).hexdigest(), codepath, fin)
    os.chdir(currentDirectory)
    sys.path = currentPath
    return module
  finally:
    if fin:
      fin.close()

def createNextTimer(next, slide):
  """Schedule a timer for the next slide transition.

  Args:
     next: (method) Function to call when the timer fires
     slide: (Clutter Slide) Slide object to read duration from
  """
  # This needs some sort of lock, but the one in place before was very
  # susceptible to a race condition. I'd rather have things simple and
  # add an effective one later. For now though, this function is never
  # called in a way that'll cause two timers to be active at once.
  if not (slide is None) and FLAGS.enabletimers:
    gobject.timeout_add(slide.duration * 1000, next)

def safeAddSlide(slides, slide):
  """Add a slide to the slides list if it does not already exist there.

  Args:
     slides: (list of Clutter Slides)
     slide: (Clutter Slide) Slide to check for presence in slides
  """
  if slide.id not in map(lambda x: x.id, slides):
    logging.info('Added slide id %s to slide list' % newslideid)
    slides.append(slide)
    return True
  else:
    return False

def changeSlideOrder(slides, direction='forward'):
  """Advance the slide order in the given direction.

  Args:
     direction: (string) either forward or backward for rotation direction
  """
  if direction == 'forward':
    slides.append(slides.pop(0))
  else:
    slides.insert(0, slides.pop())
  logSlideOrder(slides)

def logSlideOrder(slides):
  """Create a log message with the current slide order list.

  Args:
     slides: (list of Clutter Slides)
  """
  il = []
  for i in slides:
    il.append(i.id)
  logging.info('current order: %s' % str(il))

def isEmpty(slides):
  """Determines if slides is empty.
  
  Args:
     slides: (list of Clutter Slides)

  Returns:
     Boolean True/False indicating if slides is empty
  """
  return not slides

def currentSlide(slides):
  """Get the current slide from slides.

  Args:
     slides: (list of Clutter Slides)

  Returns:
     Clutter Slide that is currently active
  """
  if len(slides) > 0:
    return slides[0]

def loadNextAndPaint(current, last, stage, slides):
  """Prepare and paint the next slide.
  
  Args:
     current: (Clutter Slide)
     last: (Clutter Slide)
     stage: (Clutter Stage)
     slides: (list of Clutter Slides)

  Returns:
     Tuple with the current and last clutter slides in the deck
  """
  if current and (len(slides) > 1):
    (current, last) = loadNext(current, last, stage, slides)
    paint(current, stage)
  return current, last

def setupAnimation(current, stage):
  """Setup the intro animation for the current slide.
  
  Args:
     current: (Clutter Slide) The current slide in the deck
     stage: (Clutter Stage)
  """
  logging.debug('Setting up animation')
  if current.transition == "fade":
    current.set_opacity(0)
  elif(current.transition == "slide-right-left"):
    current.set_x(0 - stage.get_width())
  elif(current.transition == "slide-left-right"):
    current.set_x(stage.get_width())
  elif(current.transition == "slide-up-down"):
    current.set_y(0 - stage.get_height())
  elif(current.transition == "slide-down-up"):
    current.set_y(stage.get_height())

def inAnimation(current):
  """Run the intro animation of the current slide.

  Args:
     current: (Clutter Slide) The current slide in the deck
  """
  logging.debug('in animation')
  timeline = clutter.Timeline(fps=60, duration=500)
  template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
  effect = None
  if current.transition == "fade":
    effect = clutter.effect_fade(template, current, 255)
  elif ((current.transition == "slide-right-left") or
        (current.transition == "slide-left-right") or
        (current.transition == "slide-up-down") or
        (current.transition == "slide-down-up")):
    effect = clutter.effect_move(template, current, 0, 0)
  if effect:
    effect.start()

def outAnimation(current, stage):
  """Run the exit animation of the current slide.
  
  Args:
     current: (Clutter Slide) The current slide in the deck
     stage: (Clutter Stage)
  """
  logging.debug('out animation')
  timeline = clutter.Timeline(fps=60, duration=500)
  template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
  effect = None
  if (current.transition == "fade"):
    effect = clutter.effect_fade(template, current, 0)
  elif(current.transition == "slide-right-left"):
    effect = clutter.effect_move(template, current,
                                 stage.get_width(), 0)
  elif(current.transition == "slide-left-right"):
    effect = clutter.effect_move(template, current,
                                 0 - stage.get_width(), 0)
  elif(current.transition == "slide-up-down"):
    effect = clutter.effect_move(template, current,
                                 0, stage.get_height())
  elif(current.transition == "slide-down-up"):
    effect = clutter.effect_move(template, current,
                                 0, 0 - stage.get_height())
  if effect:
    effect.start()

def loadNext(current, last, stage, slides):
  """Prepare the next slide to be painted.
  
  Args:
     current: (Clutter Slide) The current slide in the deck
     last: (Clutter Slide)
     stage: (Clutter Stage)
     stage: (Clutter Stage)
  """

  if hasattr(current, 'teardownslide'):
    logging.info('Trying teardown on %s' % current.id)
    try:
      current.teardownslide()
    except Exception, e:
      logging.error('Failed to teardown slide with defined teardown method: '+e)

  if len(slides) > 1:
    outAnimation(current, stage)
    if last:
      last.hide_all()
      stage.remove(last)
    last = current
  changeSlideOrder(slides, direction='forward')
  current = currentSlide(slides)

  if hasattr(current, 'setupslide'):
    logging.info('Trying setup on %s' % current.id)
    try:
      current.setupslide()
    except Exception, e:
      logging.error('Failed to setup slide with defined setupslide method: '+e)

  if len(slides) > 1:
    setupAnimation(current, stage)

  return (current, last)

def paint(current, stage):
  """Paint the next slide to the screen.
  
  Args:
     current: (Clutter Slide)
     stage: (Clutter Stage)
  """
  inAnimation(current)
  current.show_all()
  stage.add(current)
