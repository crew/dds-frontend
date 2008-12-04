#!/usr/bin/python
import json
import logging
import clutter
import os
from clutter import Script
from slide import Slide

class Slideshow():
  """Handles the painting and parsing of slides"""

  slides = []

  def __init__(self, stage):

    self.stage = stage
    self.current = None
    self.last = None

  def isEmpty(self):
    return len(self.slides) == 0

  def parseLayout(self, file, directory):
    """Parses the given file into a slide"""

    logging.debug('Parsing layout file: %s dir: %s' % (file, directory))
    script = Script()
    script.load_from_file(file)
    slide = script.get_object('slide')
    for child in slide.get_children():
      child.set_x(child.get_x() * (self.stage.get_width() / 16))
      child.set_y(child.get_y() * (self.stage.get_height() / 9))
      child.set_width(child.get_width() * (self.stage.get_width() / 16))
      child.set_height(child.get_height() * (self.stage.get_height() / 9))
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
      self.slides.append(slide)
      logging.debug('Trying to safely add slide id %s' % id)
      added = self._safeAddSlideToDeck(slide)
      if added:
        logging.debug('safely added slide id %s' % id)
      if not self.current:
        self.current = self.currentSlide()
        logging.debug('starting slider')
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
      logging.debug('When trying to add slide id %s, we did it!!!' %
                    newslideid)
      self.slides.append(slide)
      return True

  def removeSlide(self, id):
    """Remove the slide with the given id from the cache"""
    logging.debug('I was told to remove slide id %s from the deck' % id)
    for slide in self.slides:
      if slide.id == id:
        logging.debug('Removing slide %s from the deck' % id)
        self.slides.remove(slide)

  def nextSlide(self):
    """Rotate the next slide to the front of the list"""
    logging.debug('nextSlide updating self.slides')
    self.slides.append(self.slides.pop(0))
    il = []
    for i in self.slides:
      il.append(i.id)
    logging.debug('new order: %s' % str(il))

  def currentSlide(self):
    """Return the current slide"""
    logging.debug('querying current slide')

    if len(self.slides) > 0:
      return self.slides[0]
    else:
      None

  def next(self):
    """Prepare and paint the next slide"""
    logging.debug('slideshow next')
    if self.current and (len(self.slides) > 1):
      logging.debug('slideshow next -- executing code')
      self.load_next()
      self.paint()

  def setup_animation(self):
    """Setup the intro animation for the current slide"""

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

    self.out_animation()
    if self.last:
      self.last.hide_all()
      self.stage.remove(self.last)
    self.last = self.current
    self.nextSlide()
    self.current = self.currentSlide()
    self.setup_animation()


  def paint(self):
    """Paint the next slide to the screen"""
    logging.debug('slideshow.paint method begin')
    self.in_animation()
    self.current.show_all()
    self.stage.add(self.current)
