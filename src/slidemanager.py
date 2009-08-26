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

import slideobject

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
    self._paintran = False
    self._active = False
    self._slides = []
    self._timers = {}
    self.xmpphandler = None
    self.log = logging.getLogger('slidemanager')

  ## State/Status methods
  #######################
  def IdExists(self, slideid):
    """Determine if a slide id exists in the slide list.

    Args:
       slideid: (int) slide ID

    Returns:
       Boolean True if slide exists, False otherwise
    """
    return slideid in map(lambda x: x.ID(), self._slides)

  def IsActive(self):
    """Determines if this slider's active."""
    return self._active

  def HasMultipleSlides(self):
    """Determine if we have more than one slide and should transition."""
    return len(self._slides) > 1

  def Stop(self):
    """Stops the Slideshow"""
    self.log.debug('slider stop')
    self._active = False

  def LogSlideOrder(self):
    """Create a log message with the current slide order list."""
    msg = 'Current Slide Order: %s' % str(map(lambda x: x.ID(), self._slides))
    self.log.info(msg)
    return msg

  def IsEmpty(self):
    """Determines if slides is empty.
    
    Returns:
      Boolean True/False indicating if slides is empty
    """
    return not self._slides

  def CurrentSlide(self):
    """Get the current slide from slides.

    Returns:
      Clutter Slide that is currently active
    """
    if len(self._slides) > 0:
      return self._slides[0]

  def PreviousSlide(self):
    """Get the previously shown slide from slides.

    Returns:
      Clutter Slide that was just shown
    """
    if len(self._slides) > 0:
      return self._slides[self._slides.index(self.CurrentSlide())-1]

  def UpdateSlide(self, slidetuple):
    """Using a slide manifest tuple, update it.

    Args:
       slidetuple: 
    """
    for slide in self._slides:
      if slide.CanUpdateManifest(slidetuple):
        self.log.info('Updating slide %s with new manifest' % slide.ID())
        slide.UpdateManifest(slidetuple)

  def SetXMPPHandler(self, handler):
    """Set the XMPP Thread bound to this slide manager.

    Args:
       handler: XMPPThread instance
    """
    self.xmpphandler = handler

  def AddSlide(self, slidetuple, start=True):
    """Add a new slide to the internal cache.

    Args:
      slideobj: (Slide) Slide to add to deck
      start: (boolean) if true, start the show if not already active
    """
    newslide = slideobject.Slide.CreateSlideWithManifest(slidetuple)
    self.AddSlideObject(newslide, start=start)
 
  def AddSlideObject(self, newslide, start=True):
    """Add a slide object to the slide list.

    Args:
       newslide: (Slide) Object to add
       start: (Boolean) Starts the slideshow if true.
    """
    if newslide.Parse():
      self.SafeAddSlide(newslide)
      if start and not self.IsActive():
        self.Start()

  def RemoveSlide(self, removalid):
    """Remove the slide with the given id from the cache

    Args:
       removalid: (int) Slide ID to remove
    """
    if removalid not in map(lambda x: x.ID(), self._slides):
      self.log.debug(('I was told to remove slide id %s from the deck, but its'
                     ' already gone') % removalid)
    else:
      self.log.debug('I was told to remove slide id %s from the deck'
                    % removalid)
    self.LogSlideOrder()
    for slide in self._slides:
      if slide.ID() == removalid:
        if slide == self.CurrentSlide():
          self.Next()
        self.log.info('Removing slide %s from the deck' % removalid)
        slide.slide.destroy()
        self._slides.remove(slide)
        if slide in self._timers:
          del self._timers[slide]
        self.LogSlideOrder()
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
      if self.xmpphandler:
        self.xmpphandler.SetCurrentSlide(self.CurrentSlide())
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
    self.InAnimation(slide)
    slide.slide.show_all()
    self._stage.add(slide.slide)

  def ChangeSlideOrder(self, direction='forward'):
    """Advance the slide order in the given direction.

    Args:
       direction: (string) either forward or backward for rotation direction
    """
    if direction == 'forward':
      self._slides.append(self._slides.pop(0))
    else:
      self._slides.insert(0, self._slides.pop())
    self.LogSlideOrder()

  def Advance(self):
    """Forward alias for changeSlideOrder."""
    self.ChangeSlideOrder(direction='forward')

  def Rewind(self):
    """Reverse alias for changeSlideOrder."""
    self.ChangeSlideOrder(direction='reverse')

  def LoadNextAndPaint(self):
    """Prepare and paint the next slide.
    
    Returns:
      Tuple with the current and last clutter slides in the deck
    """
    if self.CurrentSlide() and not self.IsEmpty():
      self.LoadNext()
      self.Paint(self.CurrentSlide())
    return self.CurrentSlide(), self.PreviousSlide()

  def SetupAnimation(self):
    """Setup the intro animation for the current slide.
    
    Args:
    """
    current = self.CurrentSlide()
    stage = self._stage
    self.log.debug('Setting up animation')
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

  def InAnimation(self, current):
    """Run the intro animation of the current slide.

    Args:
      current: (Clutter Slide) The current slide in the deck
    """
    self.log.debug('in animation')
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


  def OutAnimation(self):
    """Run the exit animation of the self.CurrentSlide() slide."""
    self.log.debug('out animation')
    timeline = clutter.Timeline(fps=60, duration=500)
    template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
    effect = None
    if (self.CurrentSlide().transition == "fade"):
      effect = clutter.effect_fade(template, self.CurrentSlide().slide, 0)
    elif (self.CurrentSlide().transition == "slide-right-left"):
      effect = clutter.effect_move(template, self.CurrentSlide().slide,
                                  self._stage.get_width(), 0)
    elif (self.CurrentSlide().transition == "slide-left-right"):
      effect = clutter.effect_move(template, self.CurrentSlide().slide,
                                  0 - self._stage.get_width(), 0)
    elif (self.CurrentSlide().transition == "slide-up-down"):
      effect = clutter.effect_move(template, self.CurrentSlide().slide,
                                  0, self._stage.get_height())
    elif (self.CurrentSlide().transition == "slide-down-up"):
      effect = clutter.effect_move(template, self.CurrentSlide().slide,
                                  0, 0 - self._stage.get_height())
    if effect:
      effect.start()

  def LoadNext(self):
    """Prepare the next slide to be painted."""

    try:
      self.CurrentSlide().teardownslide()
    except Exception, e:
      self.log.error('Failed to teardown slide with defined teardown method: %s'
                     % (str(e)))

    if self.HasMultipleSlides():
      self.OutAnimation()
      if self.PreviousSlide():
        self.PreviousSlide().slide.hide_all()
        self._stage.remove(self.PreviousSlide().slide)
    self.Advance()

    try:
      self.CurrentSlide().setupslide()
    except Exception, e:
      self.log.error('Failed to setup slide with defined setupslide method: %s'
                     % (str(e)))

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
    if slide.ID() not in map(lambda x: x.ID(), self._slides):
      self.log.info('Added slide id %s to slide list' % slide.ID())
      self.ResizeSlide(slide.slide)
      self._slides.append(slide)
      return True
    else:
      return False

  def ResizeSlide(self, slide):
    """Resize the given slide to fit the stage."""
    self.log.debug('Start resize')
    # find the ratio based on width
    # slide.set_size(FLAGS.ratiowidth, FLAGS.ratioheight)
    width, height = self._stage.get_size()
    ratio_w = float(width) / FLAGS.ratiowidth
    ratio_h = float(height) / FLAGS.ratioheight
    slide.set_anchor_point(0, 0)
    
    if FLAGS.letterbox:
      # TODO support letterboxing on the side, i.e. 4 x 3 shown in 16 x 10
      # anchor at top left, then scale.
      slide.set_scale(ratio_w, ratio_w)
      # letterboxing
      new_height = ratio_w * FLAGS.ratioheight
      h_diff = (height - new_height) / 2
      self.log.info('hdiff = %d' % h_diff)
      slide.move_by(0, h_diff)

      noclip = False
      # XXX Hack to support video letterboxing, sort of
      try:
        for child in slide.get_children():
          if child.__class__.__name__ == 'VideoTexture':
            child.move_by(0, h_diff * 1.5)
            noclip = True
      except:
        pass

      # XXX clips the slide to fit the letterbox format
      if not noclip:
        slide.set_clip(0, 0, slide.get_width(), slide.get_height())
    else:
      slide.set_scale(ratio_w, ratio_h)
    self._stage.queue_redraw()
    self.log.debug('%d %d' % slide.get_position())
    self.log.debug('%d %d' % slide.get_size())
    self.log.debug('End resize')
    return slide

