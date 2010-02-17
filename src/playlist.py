#!/usr/bin/env python
# vim: set shiftwidth=4 tabstop=4 softtabstop=4 :
"""slide playlist
"""

import gflags
import logging
import thread
import random

FLAGS = gflags.FLAGS

class SlideItem(object):
    def __init__(self, position, ids, weights, mode):
        self.position = position
        self.ids = ids
        self.weights = weights
        self.mode = mode
        if not self.ids:
            self.choicelist = self.ids
        else:
            self.choicelist = None

    def safepick(self, l):
        if l and len(l) > 1:
            return random.choice(l)
        elif l:
            return l[0]

    def slide(self):
        return self.safepick(self.ids)

class SingleSlideItem(SlideItem):
    pass

class RandomSlideItem(SlideItem):
    def slide(self):
        return self.sa
        if self.ids:
            return random.choice(self.ids)

class WeightedSlideItem(SlideItem):
    def buildchoicelist(self):
        if self.choicelist is None:
            self.choicelist = []
            for x in range(len(self.ids)):
                self.choicelist.update(self.ids[x]*self.weights[x])

    def slide(self):
        return self.safepick(self.choicelist)

class Playlist(object):
    def __init__(self):
        self.items = []
        self.lock = thread.allocate_lock()
        self.log = logging.getLogger('playlist')
        self.currentid = None

    def empty(self):
        self.log.debug('Checking if empty')
        with self.lock:
            return not bool(self.items)

    def has_multiple(self):
        self.log.debug('Checking has multiple')
        with self.lock:
            return len(self.items) > 1

    def rotate(self, direction='forward'):
        if self.empty():
            return
        with self.lock:
            if direction == 'forward':
                self.items.append(self.items.pop(0))
            else:
                self.items.insert(0, self.items.pop())
    
    def advance(self):
        self.rotate(direction='forward')
        self.currentid = None

    def rewind(self):
        self.rotate(direction='reverse')
        self.currentid = None

    def purge(self):
        self.items = []

    def current_slide(self):
        if self.currentid is None:
            self.currentid = self.items[0].slide()
            self.log.debug('Playlist picked %d' % self.currentid)
        return self.currentid

    def add(self, itm):
        plclass = {'single':SingleSlideItem, 'random':RandomSlideItem,
                   'weighted':WeightedSlideItem}
        item = plclass[itm['mode']](itm['position'], itm['slides'],
                                    itm['weights'], itm['mode'])
        with self.lock:
            self.items.append(item)
