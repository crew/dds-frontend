#!/usr/bin/python
import json
import logging
import clutter
import os
import gobject
import config
from clutter import Script

L_HEIGHT = 12
W_HEIGHT = 9

class Slider():
  '''Handles the painting and parsing of slides'''

  def __init__(self, stage, letterbox=False, timersenabled=True):
    self._stage = stage
    self._current = None
    self._last = None
    self._paintran = False
    self._letterbox = letterbox
    self._timersenabled = timersenabled
    self._scheduled_timer = False
    self._active = False
    self._slides = []

  def start(self):
    '''Starts the Slider, should only be called when there are slides'''
    logging.debug('slider start')
    self._active = True
    self._setupAnimation()
    self._resetTimer()
    self._paint()

  def stop(self):
    '''Stops the Slideshow'''
    logging.debug('slider stop')
    self._active = False

  def currentSlide(self):
    '''Return the current slide'''

    if len(self._slides) > 0:
      return self._slides[0]

  def isEmpty(self):
    """Determines if this slider's empty"""
    return not self._slides

  def isActive(self):
    """Determines if this slider's active"""
    return self._active

  def addSlide(self, id, duration, priority):
    '''Add a new slide to the internal cache'''
    directory = "%s/%s" % (config.option("cache"), str(id))
    layoutfile = '%s/%s' % (directory, 'layout.js')
    if os.path.exists(layoutfile):
      slide = self._parseLayout(layoutfile, directory)
      slide.id = id
      slide.duration = duration
      slide.priority = priority
      added = self._safeAddSlideToDeck(slide)
      if not self._current:
        self._current = self.currentSlide()
        self.start()
      else:
        self._resetTimer()
      return False
    else:
      return True

  def removeSlide(self, id):
    '''Remove the slide with the given id from the cache'''
    removalid = id
    logging.debug('I was told to remove slide id %s from the deck' % removalid)
    self._logSlideOrder()
    for slide in self._slides:
      if slide.id == removalid:
        logging.info('Removing slide %s from the deck' % removalid)
        self._slides.remove(slide)
        self._logSlideOrder()

  def next(self):
    '''Runs the timer thread for, and shows the next slide'''
    logging.debug('slider next')
    if self.isEmpty() or not self.isActive():
      # We don't have any slides, there is nothing to do!
      return False
    self._scheduled_timer = False
    self._loadNextAndPaint()
    self._resetTimer()
    return False

  def _parseLayout(self, file, directory):
    '''Parses the given file into a slide'''

    logging.debug('Parsing layout file: %s dir: %s' % (file, directory))
    script = Script()
    script.add_search_paths(directory)
    script.load_from_file(file)
    slide = script.get_object('slide')
    for child in slide.get_children():
      if (self._letterbox):
        letterbox_y = (self._stage.get_height() / L_HEIGHT) * 1.5
        height_div = L_HEIGHT
      else:
        letterbox_y = 0
        height_div = W_HEIGHT
      child.set_x(child.get_x() * (self._stage.get_width() / 16))
      child.set_y(letterbox_y + child.get_y() * (self._stage.get_height() / height_div))
      child.set_width(child.get_width() * (self._stage.get_width() / 16))
      child.set_height(child.get_height() * (self._stage.get_height() / height_div))
    return slide

  def _createNextTimer(self, time_in_seconds):
    """Creates a new timer if there isn't already a scheduled timer"""
    if not self._scheduled_timer:
      self._scheduled_timer = True
    else:
      return False
    # Time in milliseconds
    timertimetolive = 1000 * time_in_seconds
    gobject.timeout_add(timertimetolive, self.next)
    return True

  def _resetTimer(self):
    '''Runs the next timer thread to change slides'''
    # TODO: Make sure that self.scheduled_timer is not set for too long
    # (ie, stale lock)
    logging.debug('slider resetTimer')
    if not self._timersenabled:
      return False
    if (self.currentSlide() is not None):
      slideduration = self.currentSlide().duration
      if not self._createNextTimer(slideduration):
        logging.debug('Cannot schedule, already scheduled')

  def _safeAddSlideToDeck(self, slide):
    '''
    Check to see if the given slide, (its id really)
    already exists in the slide deck. If it does, do not re-add it
    '''
    newslideid = slide.id
    addit = True
    for deckslide in self._slides:
      if deckslide.id == newslideid:
        addit = False
        return False
    if addit:
      logging.info('Added slide id %s to slide list' % newslideid)
      self._slides.append(slide)
      return True

  def _changeSlideOrder(self, direction='forward'):
    '''
    Rotate to the next slide in the given direction
    '''
    if direction == 'forward':
      self._slides.append(self._slides.pop(0))
    else:
      self._slides.insert(0, self._slides.pop())
    self._logSlideOrder()

  def _logSlideOrder(self):
    il = []
    for i in self._slides:
      il.append(i.id)
    logging.info('current order: %s' % str(il))

  def _loadNextAndPaint(self):
    '''Prepare and paint the next slide'''
    if self._current and (len(self._slides) >= 1):
      self._loadNext()
      self._paint()

  def _setupAnimation(self):
    '''Setup the intro animation for the current slide'''
    # TODO: Update this for the new layout format

    logging.debug('Setting up animation')
    if True:
      #(self.current.transition == "fade"):
      self._current.set_opacity(0)
    elif(self._current.transition == "slide-right-left"):
      self._current.set_x(0 - self._stage.get_width())
    elif(self._current.transition == "slide-left-right"):
      self._current.set_x(self._stage.get_width())
    elif(self._current.transition == "slide-up-down"):
      self._current.set_y(0 - self._stage.get_height())
    elif(self._current.transition == "slide-down-up"):
      self._current.set_y(self._stage.get_height())

  def _inAnimation(self):
    '''Run the intro animation of the current slide'''
    # TODO: Update this for the new layout format

    logging.debug('in animation')
    timeline = clutter.Timeline(fps=60, duration=500)
    template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
    effect = None
    if True:
      #(self.current.transition == "fade"):
      effect = clutter.effect_fade(template, self._current, 255)
    elif((self._current.transition == "slide-right-left") or
         (self._current.transition == "slide-left-right") or
         (self._current.transition == "slide-up-down") or
         (self._current.transition == "slide-down-up")):
      effect = clutter.effect_move(template, self._current, 0, 0)

    if(effect):
      effect.start()

  def _outAnimation(self):
    '''Run the exit animation of the current slide'''
    # TODO: Update this for the new layout format
    logging.debug('out animation')
    timeline = clutter.Timeline(fps=60, duration=500)
    template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
    effect = None
    if True:
      #(self.current.transition == "fade"):
      effect = clutter.effect_fade(template, self._current, 0)
    elif(self._current.transition == "slide-right-left"):
      effect = clutter.effect_move(template, self._current,
                                   self._stage.get_width(), 0)
    elif(self._current.transition == "slide-left-right"):
      effect = clutter.effect_move(template, self._current,
                                   0 - self._stage.get_width(), 0)
    elif(self._current.transition == "slide-up-down"):
      effect = clutter.effect_move(template, self._current,
                                   0, self._stage.get_height())
    elif(self._current.transition == "slide-down-up"):
      effect = clutter.effect_move(template, self._current,
                                   0, 0 - self._stage.get_height())

    if (effect):
      effect.start()

  def _loadNext(self):
    '''Prepare the next slide to be painted'''
    if len(self._slides) > 1:
      self._outAnimation()
      if self._last:
        self._last.hide_all()
        self._stage.remove(self._last)
    self._last = self._current
    self._changeSlideOrder(direction='forward')
    self._current = self.currentSlide()
    if len(self._slides) > 1:
      self._setupAnimation()


  def _paint(self):
    '''Paint the next slide to the screen'''
    if len(self._slides) >1 or not self._paintran:
      self._paintran = True
      self._inAnimation()
      self._current.show_all()
      self._stage.add(self._current)
