#!/usr/bin/python
import json
import logging
import clutter
import os
import gobject
from clutter import Script

L_HEIGHT = 12
W_HEIGHT = 9

class Slider():
  '''Handles the painting and parsing of slides'''

  def __init__(self, stage, letterbox=False, timersenabled=True):
    self.stage = stage
    self.current = None
    self.last = None
    self._paintran = False
    self._letterbox = letterbox
    self._timersenabled = timersenabled
    self._scheduled_timer = False
    self.slides = []

  def start(self):
    """Starts the Slider, should only be called when there are slides"""
    logging.debug('slider start')
    self.active = True
    self.setup_animation()
    self.reset_timer()
    self.paint()

  def stop(self):
    """Stops the Slideshow"""
    logging.debug('slider stop')
    self.active = False

  def reset_timer(self):
    """Runs the next timer thread to change slides"""
    # TODO: Make sure that self.scheduled_timer is not set for too long 
    # (ie, stale lock)
    logging.debug('slider reset_timer')
    if not self._timersenabled:
      return False
    if (self.currentSlide() is not None) and (not self._scheduled_timer):
      self._scheduled_timer = True
      gobject.timeout_add(1000*self.currentSlide().duration, self.next)
    elif self._scheduled_timer:
      logging.debug('Cannot schedule, already scheduled')

  def next(self):
    """Runs the timer thread for, and shows the next slide"""
    logging.debug('slider next')
    if self.isEmpty() or not self.active:
      # We don't have any slides, there is nothing to do!
      return False
    self._scheduled_timer = False
    self.loadNextAndPaint()
    self.reset_timer()
    return False

  def isEmpty(self):
    return not self.slides

  def parseLayout(self, file, directory):
    """Parses the given file into a slide"""

    logging.debug('Parsing layout file: %s dir: %s' % (file, directory))
    script = Script()
    script.add_search_paths(directory)
    script.load_from_file(file)
    slide = script.get_object('slide')
    for child in slide.get_children():
      if (self._letterbox):
        letterbox_y = (self.stage.get_height() / L_HEIGHT) * 1.5
        height_div = L_HEIGHT
      else:
        letterbox_y = 0
        height_div = W_HEIGHT
      child.set_x(child.get_x() * (self.stage.get_width() / 16))
      child.set_y(letterbox_y + child.get_y() * (self.stage.get_height() / height_div))
      child.set_width(child.get_width() * (self.stage.get_width() / 16))
      child.set_height(child.get_height() * (self.stage.get_height() / height_div))
    return slide

  def addSlide(self, id, duration, priority, assets, directory):
    """Add a new slide to the interal cache"""

    logging.debug('Adding New Slide')
    layoutfile = directory + "/layout.js"
    if os.path.exists(layoutfile):
      logging.debug('calling parseLayout for %s' % layoutfile)
      slide = self.parseLayout(directory + "/layout.js", directory)
      slide.id = id
      slide.duration = duration
      slide.priority = priority
      logging.debug('Trying to safely add slide id %s' % id)
      added = self._safeAddSlideToDeck(slide)
      if added:
        logging.debug('safely added slide id %s' % id)
        self.logSlideOrder()
      if not self.current:
        self.current = self.currentSlide()
        logging.debug('starting slideshow')
        self.start()
      logging.debug('Telling gobject to stop calling us')
      return False
    else:
      logging.debug('Telling gobject to keep calling us')
      return True

  def _safeAddSlideToDeck(self, slide):
    ''' Check to see if the given slide, (its id really)
    already exists in the slide deck. If it does, do not re-add it
    '''
    newslideid = slide.id
    addit = True
    for deckslide in self.slides:
      if deckslide.id == newslideid:
        logging.debug('When trying to add slide id %s, we found it already' %
                      newslideid)
        addit = False
        return False
    if addit:
      logging.info('When trying to add slide id %s, we did it!!!' %
                    newslideid)
      self.slides.append(slide)
      return True

  def _intFromDictOrInt(self, input):
    if type({}) == type(input):
      return int(input['id'])
    else:
      return int(input)

  def removeSlide(self, id):
    """Remove the slide with the given id from the cache"""
    removalid = self._intFromDictOrInt(id)
    logging.debug('I was told to remove slide id %s from the deck' % removalid)
    self.logSlideOrder()
    for slide in self.slides:
      if self._intFromDictOrInt(slide.id) == removalid:
        logging.info('Removing slide %s from the deck' % removalid)
        self.slides.remove(slide)
        #if self.isEmpty():
        #  self.stage.remove_all()
        self.logSlideOrder()

  def nextSlide(self):
    """Rotate the next slide to the front of the list"""
    logging.debug('nextSlide updating self.slides')
    self.slides.append(self.slides.pop(0))
    self.logSlideOrder()

  def logSlideOrder(self): 
    il = []
    for i in self.slides:
      il.append(i.id)
    logging.info('current order: %s' % str(il))

  def currentSlide(self):
    """Return the current slide"""
    logging.debug('querying current slide')

    if len(self.slides) > 0:
      return self.slides[0]

  def loadNextAndPaint(self):
    """Prepare and paint the next slide"""
    if self.current and (len(self.slides) >= 1):
      self.load_next()
      self.paint()

  def setup_animation(self):
    """Setup the intro animation for the current slide"""
    # TODO: Update this for the new layout format

    logging.debug('Setting up animation')
    if True:
      #(self.current.transition == "fade"):
      self.current.set_opacity(0)
    elif(self.current.transition == "slide-right-left"):
      self.current.set_x(0 - self.stage.get_width())
    elif(self.current.transition == "slide-left-right"):
      self.current.set_x(self.stage.get_width())
    elif(self.current.transition == "slide-up-down"):
      self.current.set_y(0 - self.stage.get_height())
    elif(self.current.transition == "slide-down-up"):
      self.current.set_y(self.stage.get_height())

  def in_animation(self):
    """Run the intro animation of the current slide"""
    # TODO: Update this for the new layout format

    logging.debug('in animation')
    timeline = clutter.Timeline(fps=60, duration=500)
    template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
    effect = None
    if True:
      #(self.current.transition == "fade"):
      effect = clutter.effect_fade(template, self.current, 255)
    elif((self.current.transition == "slide-right-left") or
         (self.current.transition == "slide-left-right") or
         (self.current.transition == "slide-up-down") or
         (self.current.transition == "slide-down-up")):
      effect = clutter.effect_move(template, self.current, 0, 0)

    if(effect):
      effect.start()

  def out_animation(self):
    """Run the exit animation of the current slide"""
    # TODO: Update this for the new layout format
    logging.debug('out animation')
    timeline = clutter.Timeline(fps=60, duration=500)
    template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
    effect = None
    if True:
      #(self.current.transition == "fade"):
      effect = clutter.effect_fade(template, self.current, 0)
    elif(self.current.transition == "slide-right-left"):
      effect = clutter.effect_move(template, self.current,
                                   self.stage.get_width(), 0)
    elif(self.current.transition == "slide-left-right"):
      effect = clutter.effect_move(template, self.current,
                                   0 - self.stage.get_width(), 0)
    elif(self.current.transition == "slide-up-down"):
      effect = clutter.effect_move(template, self.current,
                                   0, self.stage.get_height())
    elif(self.current.transition == "slide-down-up"):
      effect = clutter.effect_move(template, self.current,
                                   0, 0 - self.stage.get_height())

    if (effect):
      effect.start()

  def load_next(self):
    """Prepare the next slide to be painted"""

    logging.debug('slideshow load_next')
    if len(self.slides) > 1:
      self.out_animation()
    if self.last and (len(self.slides) > 1):
      self.last.hide_all()
      self.stage.remove(self.last)
    self.last = self.current
    self.nextSlide()
    self.current = self.currentSlide()
    if len(self.slides) > 1:
      self.setup_animation()


  def paint(self):
    """Paint the next slide to the screen"""
    logging.debug('slideshow.paint method begin')
    if len(self.slides) >1 or not self._paintran:
      self._paintran = True
      self.in_animation()
      self.current.show_all()
      self.stage.add(self.current)
