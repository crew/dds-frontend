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

    def set_xmpp_handler(self, handler):
        self.xmpphandler = handler
    
    def add_slide(self, metadata):
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
        self.log.error('NOT IMPLEMENTED remove_slide %s' % metadata)

    def update_slide(self, metadata):
        self.log.error('NOT IMPLEMENTED update_slide %s' % metadata)
    
    
    def hide_slide(self, animation, slide):
        self.stage.remove(slide.group)
        self.log.info('afterhide')
        slide.event_afterhide()

    def fade_out_slide(self, slide):
        self.log.info('beforehide')
        slide.event_beforehide()
        if FLAGS.transitions:
            timeline = clutter.Timeline(2000)
            alpha = clutter.Alpha(timeline, clutter.EASE_OUT_QUAD)
            slide.group.set_opacity(255)
            self.fade_out_behavior = clutter.BehaviourOpacity(alpha=alpha,
                                              opacity_start=255, opacity_end=0)
            self.fade_out_behavior.apply(slide.group)
            timeline.connect('completed', self.hide_slide, slide)
            timeline.start()
        else:
            self.hide_slide(None, slide)

    def fade_in_slide(self, slide):
        self.log.info('beforeshow')
        slide.event_beforeshow()
        if FLAGS.transitions:
            timeline = clutter.Timeline(2000)
            alpha = clutter.Alpha(timeline, clutter.EASE_IN_QUAD)
            slide.group.set_opacity(0)
            self.fade_in_behavior = clutter.BehaviourOpacity(alpha=alpha,
                                             opacity_start=0, opacity_end=255)
            self.fade_in_behavior.apply(slide.group)
            timeline.start()
        else:
            slide.group.set_opacity(255)
        self.stage.add(slide.group)
        slide.group.show()
        self.log.info('aftershow')
        slide.event_aftershow()
        if self.xmpphandler is not None:
            self.xmpphandler.SetCurrentSlide(slide)

    def next(self, firsttime=False):
        if not firsttime:
            self.fade_out_slide(self.slides.current_slide())
            self.slides.advance()
        #XXX: ew.
        gobject.timeout_add(1,
                lambda:  self.fade_in_slide(self.slides.current_slide()))
        if not FLAGS.oneslide:
            gobject.timeout_add(self.slides.current_slide().duration * 1000,
                                self.next)

    def start(self):
        self.log.error('NOT IMPLEMENTED start')

    def resize_slide(self, slide):
        width, height = self.stage.get_size()
        slide.resize(width, height)

