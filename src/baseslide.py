#!/usr/bin/python
"""Slide Foundation for pythonic slides.
"""

import clutter
import gtk
import logging
import urllib2

class BaseSlide(object):
  """Base Slide Module."""

  def __init__(self):
    self.group = clutter.Group()
  
  def setupslide(self):
    pass

  def teardownslide(self):
    pass

  def TextureFromPixbuf(self, pixbuf, texture=None):
    data   = pixbuf.get_pixels()
    width  = pixbuf.get_width()
    height = pixbuf.get_height()
    has_alpha = pixbuf.get_has_alpha()
    rowstride = pixbuf.get_rowstride()
    if texture is None:
      texture = clutter.Texture()
    success = texture.set_from_rgb_data(data, has_alpha, width, height,
                                        rowstride, 4 if has_alpha else 3,
                                        clutter.TextureFlags(0))
    if not success:
      return None
    else:
      return texture

  def PixbufFromData(self, data):
    loader = gtk.gdk.PixbufLoader()
    loader.write(data)
    loader.close()
    pixbuf = loader.get_pixbuf()
    return pixbuf

  def GetDataFromURL(self, url):
    try:
      logging.info('Slide fetching data from %s' % url)
      u = urllib2.urlopen(url)
      data = u.read()
      return data
    except:
      logging.exception('Uh oh!')
      return None

  def GetTextureFromURL(self, url, texture=None):
    data = self.GetDataFromURL(url)
    if not data:
      return
    pixbuf = self.PixbufFromData(data)
    if not pixbuf:
      return
    texture = self.TextureFromPixbuf(pixbuf, texture)
    if not texture:
      return
    return texture
