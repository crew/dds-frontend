#!/usr/bin/python
"""CCIS Crew Digital Display System Frontend/Client

This module handles running the slideshow -- slide ordering, transitions, etc.
Each slide gets attached to the SlideManager to be displayed.
"""

__author__ = 'CCIS Crew <crew@ccs.neu.edu>'


import clutter
import gflags as flags
import gobject
import logging
import uuid
import time
import os
import threading

import slideobject

flags.DEFINE_boolean('resizeslides', True, 'Control resize behavior')
flags.DEFINE_integer('ratioheight', 1080, 'Height Divisor Constant')
flags.DEFINE_integer('ratiowidth', 1920, 'Width Divisor Constant')
flags.DEFINE_boolean('letterbox', False,
                     'Set the view mode to use letterboxing')
flags.DEFINE_boolean('enabletimers', True,
                     'Enable automatic slide advancement')

FLAGS = flags.FLAGS

class SlideManager(object):
  """Handles the painting and parsing of slides"""

  def __init__(self, stage):
    self._stage = stage
    self._active = False
    self._timers = {}
    self.xmpphandler = None
    self.log = logging.getLogger('slidemanager')
    ## Slide
    self.slides = []
    self.slide_lock = threading.Lock()

  def RemoveSlide(self, removalid):
    """Remove the slide with the given id from the cache

    Args:
       removalid: (int) Slide ID to remove
    """
    if removalid not in self.SlideIDList():
      self.log.debug(('I was told to remove slide id %s from the deck, but its'
                     ' already gone') % removalid)
    else:
      self.log.debug('I was told to remove slide id %s from the deck'
                    % removalid)
    self.LogSlideOrder()
    try:
      self.slide_lock.acquire()
      for slide in self.slides:
        if slide.ID() == removalid:
          if slide == self.CurrentSlide():
            self.Next()
          self.log.info('Removing slide %s from the deck' % removalid)
          slide.slide.destroy()
          self.slides.remove(slide)
          if slide in self._timers:
            del self._timers[slide]
          self.LogSlideOrder()
    finally:
      self.slide_lock.release()
    if self.IsEmpty():
      self.Stop()

  def Next(self):
    """Runs the timer thread for, and shows the next slide"""

    if not self.HasMultipleSlides():
      self.Stop()
      return

    if self.IsActive():
      if self.PreviousSlide() in self._timers:
        del self._timers[self.PreviousSlide()]
      self.LoadNextAndPaint()
      self.CreateNextTimer(self.Next, self.CurrentSlide())
    return False

  def Start(self):
    """Starts the slide manager.

    Note:
       This should only be called when there are slides
       and if the slider isn't already active.
    """
    self.log.debug('slider start')
    if self.IsActive():
      self.log.error("Attempted to start an already active slider.")
    elif self.IsEmpty():
      self.log.error("Attempted to start an empty slider.")
    else:
      self._active = True
      self.SetupAnimation()
      self.CreateNextTimer(self.Next, self.CurrentSlide())
      self.Paint(self.CurrentSlide())

  def Paint(self, slide):
    """Paint the next slide to the screen.

    Args:
       slide: (Clutter Slide)
    """
    self.log.info('starting paint')
    self._stage.add(slide.slide)
    slide.slide.show_all()
    self.InAnimation(slide)
    slide.TakeScreenshot()
    if self.xmpphandler:
      self.xmpphandler.SetCurrentSlide(self.CurrentSlide())
  def LoadNextAndPaint(self):
    """Prepare and paint the next slide.

    Returns:
      Tuple with the current and last clutter slides in the deck
    """
    if self.CurrentSlide() and not self.IsEmpty():
      self.LoadNext()
      self.Paint(self.CurrentSlide())
    return self.CurrentSlide(), self.PreviousSlide()

  def LoadNext(self):
    """Prepare the next slide to be painted."""

    if self.HasMultipleSlides():
      self.OutAnimation()

    try:
      self.CurrentSlide().teardownslide()
    except Exception:
      self.log.exception('Failed to teardown slide with teardown method.')

    self.log.info('pre advance')
    self.Advance()

    if self.HasMultipleSlides():
      if self.PreviousSlide():
        self.PreviousSlide().slide.hide_all()
        self._stage.remove(self.PreviousSlide().slide)
      else:
        self.log.warning('No previous?')

    try:
      self.log.info('Calling setupslide')
      self.CurrentSlide().setupslide()
    except Exception:
      self.log.exception('Failed to setup slide with setup method.')

    if self.HasMultipleSlides():
      self.SetupAnimation()

  def CreateNextTimer(self, nextmethod, slide):
    """Schedule a timer for the next slide transition.

    Args:
      nextmethod: (method) Function to call when the timer fires
      slide: (Clutter Slide) Slide object to read duration from
    """
    # This needs some sort of lock, but the one in place before was very
    # susceptible to a race condition. I'd rather have things simple and
    # add an effective one later. For now though, this function is never
    # called in a way that'll cause two timers to be active at once.
    if not (slide is None) and FLAGS.enabletimers:
      self.log.info('Scheduling timer for slide %s in %ss'
                    % (slide.ID(), slide.duration))

      nextuuid = str(uuid.uuid4())
      # pylint: disable-msg=C0103
      def conditionalnext():
        """On demand method for a next() call."""
        if nextuuid in self._timers.values():
          self.log.info('Hitting next')
          nextmethod()
          if slide in self._timers:
            del self._timers[slide]
        else:
          self.log.info('Would hit next, but our slide vanished')

      self._timers[slide] = nextuuid

      gobject.timeout_add(slide.duration * 1000, conditionalnext)

  def SafeAddSlide(self, slide):
    """Add a slide to the slides list if it does not already exist there.

    Args:
      slides: (list of Clutter Slides)
      slide: (Clutter Slide) Slide to check for presence in slides
    """
    try:
      self.slide_lock.acquire()
      if slide.ID() not in self.SlideIDList():
        self.log.info('Added slide id %s to slide list' % slide.ID())
        self.ResizeSlide(slide.slide)
        self.slides.append(slide)
        return True
      else:
        return False
    finally:
      self.slide_lock.release()
