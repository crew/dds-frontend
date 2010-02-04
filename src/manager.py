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
    
    def hide_slide(self, animation, slide):
        self.stage.remove(slide.group)
        self.log.info('afterhide')
        slide.event_afterhide()

    def move_out_slide(self, slide):
        self.log.info('beforehide')
        slide.event_beforehide()
        if FLAGS.transitions:
            timeline = clutter.Timeline(2000)
            alpha = clutter.Alpha(timeline, clutter.LINEAR)
            slide.group.set_position(0, 0)
            slide.group.set_clip(0, 0, FLAGS.targetwidth,
                                       FLAGS.targetheight)
            path = clutter.Path()
            path.add_move_to(0, 0)
            path.add_line_to(-self.stage.get_width(), 0)
            self.move_out_behavior = clutter.BehaviourPath(alpha, path)
            self.move_out_behavior.apply(slide.group)
            timeline.connect('completed', self.hide_slide, slide)
            timeline.start()
        else:
            self.hide_slide(None, slide)

    def move_in_slide(self, slide):
        slide.event_beforeshow()
        if FLAGS.transitions:
            timeline = clutter.Timeline(2000)
            alpha = clutter.Alpha(timeline, clutter.LINEAR)
            slide.group.set_clip(0, 0, FLAGS.targetwidth,
                                       FLAGS.targetheight)
            slide.group.set_position(self.stage.get_width(), 0)
            path = clutter.Path()
            path.add_move_to(self.stage.get_width(), 0)
            path.add_line_to(0, 0)
            self.move_in_behavior = clutter.BehaviourPath(alpha, path)
            self.move_in_behavior.apply(slide.group)
            timeline.start()
        else:
            slide.group.set_position(0,0)
        self.stage.add(slide.group)
        slide.group.show()
        slide.event_aftershow()
        if self.xmpphandler is not None:
            self.xmpphandler.SetCurrentSlide(slide)

    def next(self, firsttime=False):
        self.slides.log_order()
        if not firsttime:
            self.move_out_slide(self.slides.current_slide())
            self.slides.current_slide().lock.release()
            self.slides.advance()
        #XXX: ew.
        gobject.timeout_add(1,
                lambda:  self.move_in_slide(self.slides.current_slide()))
        self.slides.current_slide().lock.acquire()
        if not FLAGS.oneslide:
            gobject.timeout_add(self.slides.current_slide().duration * 1000,
                                self.next)

    def resize_slide(self, slide):
        width, height = self.stage.get_size()
        slide.resize(width, height)

