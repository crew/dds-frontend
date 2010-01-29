#!/usr/bin/python
"""Slide Foundation for pythonic slides.
"""

import clutter
import gtk
import logging
import urllib2
import htmlentitydefs
import re


class BaseSlide(object):
  """Base Slide Module."""

  def __init__(self):
    self.group = clutter.Group()
  
  def setupslide(self):
    """Hook to be called before display on screen."""
    pass

  def teardownslide(self):
    """Hook to be called after display on screen."""
    pass

  def TextureFromPixbuf(self, pixbuf, texture=None):
    """Given a pixbuf, create a clutter texture or update an existing texture.

    Args:
       pixbuf: (gtk.gdk.Pixbuf) pixbuf to translate
       texture (clutter.Texture) optionally update the given texture

    Returns:
      clutter.Texture on success, None on failure
    """

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
    """Given some image data, get a Pixbuf.

    Args:
       data: bytestring of image (png/jpg/etc) data

    Returns:
       gtk.gdk.Pixbuf
    """
    loader = gtk.gdk.PixbufLoader()
    loader.write(data)
    loader.close()
    pixbuf = loader.get_pixbuf()
    return pixbuf

  def GetDataFromURL(self, url):
    """Open a URL and get its content data.

    Args:
       url: (string) HTTP URI

    Returns:
       data string on success, None on failure
    """
    try:
      logging.info('Slide fetching data from %s' % url)
      u = urllib2.urlopen(url)
      data = u.read()
      return data
    except:
      logging.exception('Uh oh!')
      return None

  def GetTextureFromURL(self, url, texture=None):
    """Given a URL, get a clutter.Texture from its data.

    Args:
       url: (string) HTTP URI
       texture (clutter.Texture) optionally update the given texture

    Returns:
      clutter.Texture on success, None on failure
    """
    data = self.GetDataFromURL(url)
    if not data:
      return None
    pixbuf = self.PixbufFromData(data)
    if not pixbuf:
      return None
    texture = self.TextureFromPixbuf(pixbuf, texture)
    if not texture:
      return None
    return texture

  def UnescapeHTMLEntities(self, data):
    """Replace HTML entities with their unicode equivalent.

    Args:
       data: (string) text to unescape

    Returns:
       unescaped string
    """
    if '#39' not in htmlentitydefs.name2codepoint:
      htmlentitydefs.name2codepoint['#39'] = 39
    return re.sub('&(%s);' % '|'.join(htmlentitydefs.name2codepoint),
                  lambda m: unichr(name2codepoint[m.group(1)]), data)

  def RemoveHTMLTags(self, data):
    """Remove HTML tags from the given data after unescaping.
    Args:
       data: (string) text to clean

    Returns:
       cleaned string
    """
    #FIXME: eww.
    html_tag = re.compile(r'<.*?>')
    return self.UnescapeHTMLEntities(html_tag.sub('', data))
