#!/usr/bin/env python
# vim: set shiftwidth=4 tabstop=4 softtabstop=4 :
"""slide manager
"""

import gflags
import logging
import thread
import gobject

import collection
import slideobject

FLAGS = gflags.FLAGS


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
    
    def next(self, firsttime=False):
        if not firsttime:
            self.log.info('beforehide')
            self.slides.current_slide().event_beforehide()
            self.stage.remove_all()
            self.log.info('afterhide')
            self.slides.current_slide().event_afterhide()
            self.slides.advance()
        self.log.info('beforeshow')
        self.slides.current_slide().event_beforeshow()
        self.paint()
        if not FLAGS.oneslide:
            gobject.timeout_add(self.slides.current_slide().duration * 1000,
                                self.next)
        self.log.info('aftershow')
        self.slides.current_slide().event_aftershow()

    def start(self):
        self.log.error('NOT IMPLEMENTED start')

    def resize_slide(self, slide):
        width, height = self.stage.get_size()
        slide.resize(width, height)

    def paint(self):
        self.log.info('Painting %s' % self.slides.current_slide())
        self.stage.add(self.slides.current_slide().group)
        self.stage.show()
        self.xmpphandler.SetCurrentSlide(self.slides.current_slide())

