#!/usr/bin/python
import imp
import hashlib
import logging
import clutter
import os
import gobject
import config
from clutter import Script

L_HEIGHT = 12
W_HEIGHT = 9

class Slider(object):
  '''Handles the painting and parsing of slides'''

  def __init__(self, stage, letterbox=False, timersenabled=True):
    self._stage = stage
    self._current = None
    self._last = None
    self._paintran = False
    self._letterbox = letterbox
    self._timersenabled = timersenabled
    self._timer_scheduled = False
    self._active = False
    self._slides = []

  def addSlide(self, info):
    '''Add a new slide to the internal cache'''
    directory = "%s/%s" % (config.option("cache"), str(info["id"]))
    if "layout" == info["mode"]:
      layoutfile = '%s/%s' % (directory, 'layout.js')
      slide = parseLayout(layoutfile, directory, self._stage, self._letterbox)
    elif "module" == info["mode"]:
      pythonfile = '%s/%s' % (directory, 'layout.py')
      slide = parsePython(pythonfile, directory, self._stage, self._letterbox)
    elif "executable" == info["mode"]:
      pass
    else:
      return True
    slide.id = info["id"]
    slide.duration = info["duration"]
    slide.priority = info["priority"]
    slide.transition = info["transition"]
    empty = isEmpty(self._slides)
    added = safeAddSlide(self._slides, slide)
    if (self._current is None) or empty:
      self._current = currentSlide(self._slides)
      self.start()
    else:
      self._timer_scheduled = resetTimer(self.next, self._slides,
                                         self._timer_scheduled, self._timersenabled)
      return False

  def removeSlide(self, removalid):
    '''Remove the slide with the given id from the cache'''
    logging.debug('I was told to remove slide id %s from the deck' % removalid)
    logSlideOrder(self._slides)
    for slide in self._slides:
      if slide.id == removalid:
        logging.info('Removing slide %s from the deck' % removalid)
        self._slides.remove(slide)
        logSlideOrder(self._slides)
    if isEmpty(self._slides):
      self.stop()
    else:
      if not (self._current == currentSlide(self._slides)):
        self._current = currentSlide(self._slides)

  def next(self):
    '''Runs the timer thread for, and shows the next slide'''
    logging.debug('slider next')
    self._timer_scheduled = False
    if isEmpty(self._slides) or not self.isActive():
      # We don't have any slides, there is nothing to do!
      return False
    (self._current, self._last) = loadNextAndPaint(self._current, self._last,
                                                   self._stage, self._slides)
    self.timer_scheduled = resetTimer(self.next, self._slides,
                                      self._timer_scheduled, self._timersenabled)
    return False

  def start(self):
    '''Starts the Slider, should only be called when there are slides'''
    logging.debug('slider start')
    self._active = True
    setupAnimation(self._current, self._stage)
    self._timer_scheduled = resetTimer(self.next, self._slides,
                                       self._timer_scheduled, self._timersenabled)
    paint(self._current, self._stage)

  def stop(self):
    '''Stops the Slideshow'''
    logging.debug('slider stop')
    self._active = False

  def isActive(self):
    """Determines if this slider's active"""
    return self._active

def parseLayout(file, directory, stage, letterbox):
  '''Parses the given json file into a slide'''
  logging.debug('Parsing layout file: %s dir: %s' % (file, directory))
  script = Script()
  script.add_search_paths(directory)
  script.load_from_file(file)
  slide = script.get_object('slide')
  return setupNewSlide(slide, stage, letterbox)

def parsePython(file, directory, stage, letterbox):
  """Returns a slide from the given python module"""
  slideModule = loadModule(file, directory)
  return setupNewSlide(slideModule.slide, stage, letterbox)

def setupNewSlide(slide, stage, letterbox):
  """Sets the correct height and width for the given freshly parsed slide"""
  for child in slide.get_children():
    if (letterbox):
      letterbox_y = (stage.get_height() / L_HEIGHT) * 1.5
      height_div = L_HEIGHT
    else:
      letterbox_y = 0
      height_div = W_HEIGHT
      child.set_x(child.get_x() * (stage.get_width() / 16))
      child.set_y(letterbox_y + child.get_y() * (stage.get_height() /
                                                 height_div))
      child.set_width(child.get_width() * (stage.get_width() / 16))
      child.set_height(child.get_height() * (stage.get_height() /
                                             height_div))
  return slide

def loadModule(codepath, directory):
  """Returns the module object for the python file at the given path"""
  try:
    currentDirectory = os.getcwd()
    os.chdir(directory)
    fin = open(codepath, 'rb')
    module = imp.load_source(hashlib.sha1(codepath).hexdigest(), codepath, fin)
    os.chdir(currentDirectory)
    return module
  finally:
    fin.close()

def createNextTimer(next, timer_scheduled, time_in_seconds):
  """Creates a new timer if there isn't already a scheduled timer"""
  if timer_scheduled:
    logging.debug('Cannot schedule, already scheduled')
    return timer_scheduled
  # Time in milliseconds
  timertimetolive = 1000 * time_in_seconds
  gobject.timeout_add(timertimetolive, next)
  return True

def resetTimer(next, slides, timer_scheduled, timersenabled):
  '''Runs the next timer thread to change slides'''
  # TODO: Make sure that timer_scheduled is not set for too long
  # (ie, stale lock)
  logging.debug('slider resetTimer')
  if not(currentSlide(slides) is None) and timersenabled:
    slideduration = currentSlide(slides).duration
    logging.debug(slideduration)
    return createNextTimer(next, timer_scheduled, slideduration)
  return timer_scheduled

def safeAddSlide(slides, slide):
  '''
  Check to see if the given slide, (its id really)
  already exists in the slide deck. If it does, do not re-add it
  '''
  newslideid = slide.id
  for deckslide in slides:
    if deckslide.id == newslideid:
      return False
  logging.info('Added slide id %s to slide list' % newslideid)
  slides.append(slide)
  return True

def changeSlideOrder(slides, direction='forward'):
  '''
  Rotate to the next slide in the given direction
  '''
  if direction == 'forward':
    slides.append(slides.pop(0))
  else:
    slides.insert(0, slides.pop())
  logSlideOrder(slides)

def logSlideOrder(slides):
  il = []
  for i in slides:
    il.append(i.id)
  logging.info('current order: %s' % str(il))

def isEmpty(slides):
  """Determines if slides is empty"""
  return not slides

def currentSlide(slides):
  '''Return the current slide'''
  if len(slides) > 0:
    return slides[0]

def loadNextAndPaint(current, last, stage, slides):
  '''Prepare and paint the next slide'''
  if current and (len(slides) > 1):
    (current, last) = loadNext(current, last, stage, slides)
    paint(current, stage)
    return (current, last)

def setupAnimation(current, stage):
  '''Setup the intro animation for the current slide'''
  logging.debug('Setting up animation')
  if (current.transition == "fade"):
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
  '''Run the intro animation of the current slide'''
  logging.debug('in animation')
  timeline = clutter.Timeline(fps=60, duration=500)
  template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
  effect = None
  if (current.transition == "fade"):
    effect = clutter.effect_fade(template, current, 255)
  elif((current.transition == "slide-right-left") or
       (current.transition == "slide-left-right") or
       (current.transition == "slide-up-down") or
       (current.transition == "slide-down-up")):
    effect = clutter.effect_move(template, current, 0, 0)
  if(effect):
    effect.start()

def outAnimation(current, stage):
  '''Run the exit animation of the current slide'''
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
  if (effect):
    effect.start()

def loadNext(current, last, stage, slides):
  '''Prepare the next slide to be painted'''
  if len(slides) > 1:
    outAnimation(current, stage)
    if last:
      last.hide_all()
      stage.remove(last)
    last = current
  changeSlideOrder(slides, direction='forward')
  current = currentSlide(slides)
  if len(slides) > 1:
    setupAnimation(current, stage)
  return (current, last)

def paint(current, stage):
  '''Paint the next slide to the screen'''
  inAnimation(current)
  current.show_all()
  stage.add(current)
