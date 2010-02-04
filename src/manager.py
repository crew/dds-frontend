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
        wasempty = self.slides.empty()
        self.resize_slide(o)
        self.slides.add_slide(o)
        if wasempty and not self.slides.empty():
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
    
    def advance_after_transition(self, animation, slide):
        self.stage.remove(slide.group)
        self.log.info('afterhide')
        slide.event_afterhide()
        self.slides.current_slide().lock.release()
        self.slides.advance()
        self.show_slide()

    def show_slide(self):
        gobject.timeout_add(1,
            lambda:  self.fade_in_slide(self.slides.current_slide()))
        self.slides.current_slide().lock.acquire()

    def fade_out_slide(self, slide, after):
        self.log.info('beforehide')
        slide.event_beforehide()
        if FLAGS.transitions:
            timeline = clutter.Timeline(2000)
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
            self.advance_after_transition(None, slide)

    def fade_in_slide(self, slide):
        slide.event_beforeshow()
        self.stage.add(slide.group)
        if FLAGS.transitions:
            timeline = clutter.Timeline(2000)
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
        self.slides.log_order()
        if firsttime:
            self.show_slide()
        else:
            self.fade_out_slide(self.slides.current_slide(),
                                self.advance_after_transition)
        if not FLAGS.oneslide:
            gobject.timeout_add(self.slides.current_slide().duration * 1000,
                                self.next)

    def resize_slide(self, slide):
        width, height = self.stage.get_size()
        slide.resize(width, height)

