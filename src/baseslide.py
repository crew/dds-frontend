#!/usr/bin/python
"""Slide Foundation for pythonic slides.
"""

import clutter
import gtk
import logging
import urllib
import htmlentitydefs
import re
import vobject
import pytz
import os
import datetime


class BaseSlide(object):
  """Base Slide Module."""
  def __init__(self):
    self.calendar = None
    self.calevents = None
    self.group = clutter.Group()
    self.localtime = pytz.timezone('US/Eastern')
    self.ourpath = os.path.dirname(__file__)

  def event_beforeshow(self):
    """Hook to be called before display on screen."""
    logging.warning('beforeshow undefined')

  def event_aftershow(self):
    """Hook to be called after display on screen."""
    logging.warning('aftershow undefined')

  def event_loop(self):
    """Hook to be called periodically while on screen."""
    logging.warning('loop undefined')

  def event_beforehide(self):
    """Hook to be called before removal from screen."""
    logging.warning('beforehide undefined')

  def event_afterhide(self):
    """Hook to be called after removal from screen."""
    logging.warning('afterhide undefined')

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
      u = urllib.urlopen(url)
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
                  lambda m: unichr(htmlentitydefs.name2codepoint[m.group(1)]),
                  data)

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

  def do_standalone_display(self):
    """This might be useful somewhere. (no resize)"""
    stage = clutter.Stage()
    stage.connect('destroy', clutter.main_quit)
    stage.connect('key-press-event', lambda x,y: clutter.main_quit())
    stage.set_fullscreen(True)
    stage.set_color(clutter.color_from_string('black'))
    stage.add(self.group)
    stage.show_all()
    clutter.main()

  def download_fetch_ical(self, uri, force=False):
    """Fetch an iCal feed and store it locally."""
    logging.info(self.ourpath)
    if self.calendar is None or force:
      tmpfile = os.path.join(os.path.dirname(self.ourpath), 'calcache.ics')
      fetchit = lambda: urllib.urlretrieve(uri, tmpfile)
      if not os.path.exists(tmpfile):
        fetchit()
      stats = os.stat(tmpfile)
      lmdate = datetime.datetime.fromtimestamp(stats[8], self.localtime)
      now   = datetime.datetime.now(self.localtime)
      delta = datetime.timedelta(days=1)
      if not lmdate < now+delta:
        fetchit()
      self.calendar = vobject.readOne(open(tmpfile).read())

  def update_calevents(self, within=20, mindesc=100, allday=False):
    now   = datetime.datetime.now(self.localtime)
    delta = datetime.timedelta(days=within)
    self.calevents = []

    def filterattrs(event):
      """Local helper to filter events if they are missing attrs."""
      for a in ['description', 'summary', 'location']:
        if not hasattr(event, a):
          return False
      return True

    for e in self.calendar.components():
      if not filterattrs(e):
        continue
      elif type(e.dtstart.value) != datetime.datetime:
        continue
      elif e.dtstart.value < now or e.dtstart.value > (now + delta):
        continue
      elif len(e.description.value) < mindesc:
        continue
      self.calevents.append(e)
