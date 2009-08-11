#!/usr/bin/python
import clutter
import config
import gflags as flags
import gobject
import hashlib
import imp
import logging
import os
import sys

import slideobject

flags.DEFINE_integer('lheight', 1440, 'Letterbox Height Divisor Constant')
flags.DEFINE_integer('wheight', 1080, 'Widescreen Height Divisor Constant')
flags.DEFINE_integer('widthdivisor', 1920, 'Width Divisor Constant')
flags.DEFINE_boolean('letterbox', False,
                     'Set the view mode to use letterboxing')
flags.DEFINE_boolean('enabletimers', True,
                     'Control automatic slide advancement')

FLAGS = flags.FLAGS

class SlideManager(object):
  """Handles the painting and parsing of slides"""

  def __init__(self, stage):
    self._stage = stage
    self._current = None
    self._last = None
    self._paintran = False
    self._active = False
    self._slides = []

  def updateSlide(self, slidetuple):
    """Using a slide manifest tuple, update it.

    Args:
       slidetuple: 
    """
    for slide in self._slides:
      if slide.canUpdateManifest(slidetuple):
        slide.updateManifest(slidetuple)
        logging.info('Updating slide %s with new manifest' % slide.id)

  def addSlide(self, slidetuple):
    """Add a new slide to the internal cache.

    Args:
      slideobj: (Slide) Slide to add to deck
    Returns:
       False on add failure (for unsupported or improperly parsed slides)
    """
    newslide = slideobject.Slide.CreateSlideWithManifest(slidetuple)
    newslide.parse()
    
    wasempty = self.isEmpty()
    self.safeAddSlide(newslide)
    if wasempty:
      self._current = self.currentSlide()
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
    self.logSlideOrder()
    for slide in self._slides:
      if slide.id == removalid:
        if slide == self._current:
          self.next()
        logging.info('Removing slide %s from the deck' % removalid)
        slide.slide.destroy()
        self._slides.remove(slide)
        self.logSlideOrder()
    if self.isEmpty():
      self.stop()

  def next(self):
    """Runs the timer thread for, and shows the next slide"""
    logging.debug('slider next')
    if self.hasMultipleSlides() and self.isActive():
      if self._last is None:
        self._last = self._current

      self.loadNextAndPaint()
      self.createNextTimer(self.next, self._current)
    return False

  def start(self):
    """
    Starts the slider. This should only be called when there are slides
    and if the slider isn't already active.
    """
    logging.debug('slider start')
    if self.isActive():
      logging.error("Attempted to start an already active slider.")
    elif self.isEmpty():
      logging.error("Attempted to start an empty slider.")
    else:
      self._active = True
      self.setupAnimation()
      self.createNextTimer(self.next, self.currentSlide())
      self.paint(self.currentSlide())

  def idExists(self, slideid):
    """Determine if a slide id exists in the slide list.

    Args:
       slideid: (int) slide ID

    Returns:
       Boolean True if slide exists, False otherwise
    """
    return slideid in map(lambda x: x.id, self._slides)

  def stop(self):
    """Stops the Slideshow"""
    logging.debug('slider stop')
    self._active = False

  def isActive(self):
    """Determines if this slider's active."""
    return self._active

  def paint(self, slide):
    """Paint the next slide to the screen.
    
    Args:
      slide: (Clutter Slide)
    """
    logging.info('starting paint')
    self.inAnimation(slide)
    slide.slide.show_all()
    self._stage.add(slide.slide)

  def changeSlideOrder(self, direction='forward'):
    """Advance the slide order in the given direction.

    Args:
      direction: (string) either forward or backward for rotation direction
    """
    if direction == 'forward':
      self._slides.append(self._slides.pop(0))
    else:
      self._slides.insert(0, self._slides.pop())
    self.logSlideOrder()

  def advance(self):
    self.changeSlideOrder(direction='forward')

  def rewind(self):
    self.changeSlideOrder(direction='reverse')

  def logSlideOrder(self):
    """Create a log message with the current slide order list."""
    logging.info('Current Slide Order: %s'
                  % str(map(lambda x: x.id, self._slides)))

  def isEmpty(self):
    """Determines if slides is empty.
    
    Returns:
      Boolean True/False indicating if slides is empty
    """
    return not self._slides

  def currentSlide(self):
    """Get the current slide from slides.

    Returns:
      Clutter Slide that is currently active
    """
    if len(self._slides) > 0:
      return self._slides[0]

  def loadNextAndPaint(self):
    """Prepare and paint the next slide.
    
    Returns:
      Tuple with the current and last clutter slides in the deck
    """
    if self._current and not self.isEmpty():
      self.loadNext()
      self.paint(self._current)
    return self._current, self._last

  def setupAnimation(self):
    """Setup the intro animation for the current slide.
    
    Args:
    """
    current = self.currentSlide()
    stage = self._stage
    logging.debug('Setting up animation')
    if current.transition == "fade":
      current.slide.set_opacity(0)
    elif(current.transition == "slide-right-left"):
      current.slide.set_x(0 - stage.get_width())
    elif(current.transition == "slide-left-right"):
      current.slide.set_x(stage.get_width())
    elif(current.transition == "slide-up-down"):
      current.slide.set_y(0 - stage.get_height())
    elif(current.transition == "slide-down-up"):
      current.slide.set_y(stage.get_height())

  def inAnimation(self, current):
    """Run the intro animation of the current slide.

    Args:
      current: (Clutter Slide) The current slide in the deck
    """
    logging.debug('in animation')
    timeline = clutter.Timeline(fps=60, duration=500)
    template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
    effect = None
    if current.transition == "fade":
      effect = clutter.effect_fade(template, current.slide, 255)
    elif ((current.transition == "slide-right-left") or
          (current.transition == "slide-left-right") or
          (current.transition == "slide-up-down") or
          (current.transition == "slide-down-up")):
      effect = clutter.effect_move(template, current.slide, 0, 0)
    if effect:
      effect.start()


  def outAnimation(self):
    """Run the exit animation of the self.currentSlide() slide."""
    logging.debug('out animation')
    timeline = clutter.Timeline(fps=60, duration=500)
    template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
    effect = None
    if (self.currentSlide().transition == "fade"):
      effect = clutter.effect_fade(template, self.currentSlide().slide, 0)
    elif(self.currentSlide().transition == "slide-right-left"):
      effect = clutter.effect_move(template, self.currentSlide().slide,
                                  self._stage.get_width(), 0)
    elif(self.currentSlide().transition == "slide-left-right"):
      effect = clutter.effect_move(template, self.currentSlide().slide,
                                  0 - self._stage.get_width(), 0)
    elif(self.currentSlide().transition == "slide-up-down"):
      effect = clutter.effect_move(template, self.currentSlide().slide,
                                  0, self._stage.get_height())
    elif(self.currentSlide().transition == "slide-down-up"):
      effect = clutter.effect_move(template, self.currentSlide().slide,
                                  0, 0 - self._stage.get_height())
    if effect:
      effect.start()

  def hasMultipleSlides(self):
    return len(self._slides) > 1

  def loadNext(self):
    """Prepare the next slide to be painted."""

    try:
      self._current.teardownslide()
    except Exception, e:
      logging.error('Failed to teardown slide with defined teardown method: %s'
                    % (str(e)))

    if self.hasMultipleSlides():
      self.outAnimation()
      if self._last:
        self._last.slide.hide_all()
        self._stage.remove(self._last.slide)
      self._last = self._current
    self.advance()
    self._current = self.currentSlide()

    try:
      self._current.setupslide()
    except Exception, e:
      logging.error('Failed to setup slide with defined setupslide method: %s'
                    % (str(e)))

    if self.hasMultipleSlides():
      self.setupAnimation()

  def createNextTimer(self, next, slide):
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
      logging.info('Scheduling timer for slide %s in %ss'
                  % (slide.id, slide.duration))
      gobject.timeout_add(slide.duration * 1000, next)

  def safeAddSlide(self, slide):
    """Add a slide to the slides list if it does not already exist there.

    Args:
      slides: (list of Clutter Slides)
      slide: (Clutter Slide) Slide to check for presence in slides
    """
    if slide.id not in map(lambda x: x.id, self._slides):
      logging.info('Added slide id %s to slide list' % slide.id)
      self.resizeSlide(slide.slide)
      self._slides.append(slide)
      return True
    else:
      return False

  def resizeSlide(self, slide):
    """Resize the given slide to fit the stage."""
    # find the ratio based on width
    slide.set_size(1920, 1080)
    width, height = self._stage.get_size()
    ratio_w = float(width) / 1920
    ratio_h = float(height) / 1080
    new_width = ratio_w * 1920
    slide.set_anchor_point(0, 0)
    
    if FLAGS.letterbox:
      # TODO support letterboxing on the side, i.e. 4 x 3 shown in 16 x 10
      # anchor at top left, then scale.
      slide.set_scale(ratio_w, ratio_w)

      # letterboxing
      new_height = ratio_w * 1080
      h_diff = (height - new_height) / 2
      slide.move_by(0, h_diff)
      # XXX clips the slide to fit the letterbox format
      slide.set_clip(0, 0, slide.get_width(), slide.get_height())
    else:
      slide.set_scale(ratio_w, ratio_h)
    return slide
