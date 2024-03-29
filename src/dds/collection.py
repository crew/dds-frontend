#!/usr/bin/env python
# vim: set shiftwidth=4 tabstop=4 softtabstop=4 :
"""slide collection
"""

import gflags
import logging
import thread
import playlist

FLAGS = gflags.FLAGS


class Collection(object):
    def __init__(self):
        self.slides = []
        self.lock = thread.allocate_lock()
        self.log = logging.getLogger('collection')
        self.playlist = playlist.Playlist()
        self.currentid = None
        self.cachedcurrent = None

    def empty(self):
        self.log.debug('Checking if empty')
        with self.lock:
            return not bool(self.slides)

    def has_multiple(self):
        self.log.debug('Checking has multiple')
        with self.lock:
            return len(self.slides) > 1

    def rotate(self, direction='forward'):
        self.playlist.rotate(direction)

    def advance(self):
        self.rotate(direction='forward')
    
    def id_list(self):
        self.log.debug('Getting ID list')
        with self.lock:
            return [x.id() for x in self.slides]

    def id_exists(self, id):
        return id in self.id_list()

    def get_by_id(self, id):
        """Get the slide with the given id.

        Args:
           id: (int) slide id number

        Returns:
           slide object or None if not found
        """
        with self.lock:
            for slide in self.slides:
                if slide.id() == id:
                    return slide
        return None

    def log_order(self):
        """Log the current slide order to info log."""
        self.log.info('Current Order: %s' % self.id_list())

    def current_slide(self):
        self.log.debug('Getting current slide')
        if (self.cachedcurrent is None or
            self.currentid != self.playlist.current_slide()):
            self.currentid = self.playlist.current_slide()
            self.cachedcurrent = self.get_by_id(self.currentid)
        return self.cachedcurrent

    def add_slide(self, slideobj):
        self.log.debug('Adding slide %s' % slideobj)
        if not self.id_exists(slideobj.id()):
            with self.lock:
                self.slides.append(slideobj)
        else:
            self.log.warning('Slide %s already exists' % slideobj)

    def remove_slide(self, slideobj):
        self.log.debug('Removing slide %s' % slideobj)
        if self.id_exists(slideobj.id()):
            with self.lock:
                self.slides.remove(slideobj)
        else:
            self.log.error('Slide %s does not exist [how did this happen]'
                           % slideobj)

