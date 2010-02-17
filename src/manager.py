#!/usr/bin/env python
# vim: set shiftwidth=4 tabstop=4 softtabstop=4 :
"""slide manager
"""

import gflags
import logging
import thread
import gobject
import clutter

import collection
import slideobject

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('transitions', True, 'Fade in and out slides')

class Manager(object):
    def __init__(self, stage):
        self.slides = collection.Collection()
        self.lock = thread.allocate_lock()
        self.stage = stage
        self.log = logging.getLogger('manager')
        self.xmpphandler = None
        self.setup_fade_to_black()

    def setup_fade_to_black(self):
        self.blackfader = clutter.Rectangle()
        self.blackfader.set_position(0,0)
        self.blackfader.set_size(self.stage.get_width(),
                                 self.stage.get_height())
        self.blackfader.set_color(clutter.color_from_string("black"))
        self.stage.add(self.blackfader)

    def set_xmpp_handler(self, handler):
        self.xmpphandler = handler
    
    def add_slide(self, metadata):
        if self.slides.id_exists(metadata['id']):
            self.update_slide(metadata)
        else:
            o = slideobject.Slide.create_slide_from_metadata(metadata)
            self._add_slide(o)

    def _add_slide(self, o):
        self.log.debug('add_slide %s' % o)
        wasempty = ((self.slides.current_slide() is None) or
                    len(self.stage.get_children()) == 1) 
        self.resize_slide(o)
        self.slides.add_slide(o)
        if wasempty and self.slides.current_slide():
            self.next(firsttime=True)
    
    def remove_slide(self, metadata):
        self.log.debug('remove_slide %s' % metadata)
        slide = self.slides.get_by_id(metadata)
        if slide:
            if slide.lock.locked():
                sleeptime = 5000
                self.log.warning('Cannot remove %s, currently on screen.'
                                 ' Waiting %dms.' % (slide, sleeptime))
                gobject.timeout_add(sleeptime,
                                    lambda: self.remove_slide(metadata))
                return
            with slide.lock:
                self.slides.remove_slide(slide)
                slide.group.destroy()
                del slide

    def update_slide(self, metadata):
        self.log.debug('update_slide %s' % metadata)
        slide = self.slides.get_by_id(metadata['id'])
        if slide:
            slide.reload(metadata)
            gobject.timeout_add(2, lambda: self.resize_slide(slide))
    
    def after_transition(self, animation, slide):
        self.stage.remove(slide.group)
        slide.event_afterhide()
        if self.slides.current_slide() != slide:
            slide.lock.release()
        self.show_slide()

    def show_slide(self):
        gobject.timeout_add(1,
            lambda:  self.fade_in_slide(self.slides.current_slide()))
        gobject.timeout_add(self.slides.current_slide().duration * 1000,
                            self.next)

    def fade_out_slide(self, slide, after):
        slide.event_beforehide()
        if FLAGS.transitions:
            timeline = clutter.Timeline(500)
            alpha = clutter.Alpha(timeline, clutter.LINEAR)
            self.blackfader.set_opacity(0)
            self.fade_out_behavior = clutter.BehaviourOpacity(alpha=alpha,
                                                              opacity_start=0,
                                                              opacity_end=255)
            self.fade_out_behavior.apply(self.blackfader)
            self.blackfader.raise_top()
            self.blackfader.show()
            timeline.connect('completed', after, slide)
            timeline.start()
        else:
            self.after_transition(None, slide)

    def fade_in_slide(self, slide):
        self.stage.add(slide.group)
        if FLAGS.transitions:
            timeline = clutter.Timeline(500)
            alpha = clutter.Alpha(timeline, clutter.LINEAR)
            self.blackfader.raise_top()
            self.blackfader.show()
            self.blackfader.set_opacity(255)
            self.fade_in_behavior = clutter.BehaviourOpacity(alpha=alpha,
                                                             opacity_start=255,
                                                             opacity_end=0)
            self.fade_in_behavior.apply(self.blackfader)
            timeline.start()
        slide.group.show()
        slide.event_aftershow()
        if self.xmpphandler is not None:
            self.xmpphandler.SetCurrentSlide(slide)

    def next(self, firsttime=False):
        if firsttime:
            self.slides.current_slide().lock.acquire()
            self.slides.current_slide().event_beforeshow()
            self.show_slide()
        else:
            last_slide = self.slides.current_slide()
            self.slides.advance()
            if self.slides.current_slide() != last_slide:
                self.slides.current_slide().lock.acquire()
            self.slides.current_slide().event_beforeshow()
            self.fade_out_slide(last_slide,
                                self.after_transition)

    def resize_slide(self, slide):
        width, height = self.stage.get_size()
        slide.resize(width, height)

