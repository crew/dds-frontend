import clutter
import pango
import sys
import cgi
import feedparser
import baseslide
import logging
from htmlentitydefs import name2codepoint
# for some reason, python 2.5.2 doesn't have this one (apostrophe)
name2codepoint['#39'] = 39
# regex lib for stripping HTML tags
import re

# This class displays an RSS feed. It is strictly static content
# at the moment - however, this class is intended to be a template
# to easily incorporate ANY RSS feed into DDS, simply by initializing
# it with a different feed.
class RSSDisplay(baseslide.BaseSlide):
  def __init__(self, feedURL):
    """ Initializes the stage and score for this slide. """
    baseslide.BaseSlide.__init__(self)
    self.addrss(feedURL)
    self.feedURL = feedURL

  def setupslide(self):
    self.refresh(self.feedURL)

  def refresh(self, feedURL):
    self.group.remove_all()
    self.addrss(feedURL)

  def addrss(self, feedURL):
    """ Adds the RSS feed information to this slide. """
    #TODO: ERROR CHECKING: MAKE SURE WE DON'T EXPLODE WITH A BAD FEED
    rssfeed = feedparser.parse(feedURL)
    feedtitle = remove_html_tags(rssfeed.feed.title)
    feedtitleActor = clutter.Text()
    feedtitleActor.set_text(feedtitle)
    feedtitleActor.set_font_name("serif 71")
    feedtitleActor.set_color(clutter.color_from_string("gold"))
    feedtitleActor.set_size(1920, 100)
    feedtitleActor.set_position(0, 0)
    self.group.add(feedtitleActor) 

    y = 100
    for entry in rssfeed.entries:
      if y >= 1080:
        break
      y += self.add_entry_group(entry, y, width=1920) + 20


  def add_entry_group(self, entry, starty, width=1920):
    topstorytitle = remove_html_tags(entry.title)
    title = clutter.Text()
    title.set_font_name("serif 32")
    title.set_text(topstorytitle)
    title.set_markup('<span underline="single">%s</span>' % topstorytitle)
    title.set_width(width)
    title.set_color(clutter.color_from_string("white"))
    title.set_position(0, starty)
    self.group.add(title)

    topstorytext = remove_html_tags(entry.summary)
    content = clutter.Text()
    content.set_text(topstorytext)
    content.set_font_name("serif 24")
    content.set_line_wrap(True)
    content.set_line_wrap_mode(2)
    content.set_color(clutter.color_from_string("white"))
    content.set_position(0, starty + title.get_height())
    content.set_width(width)
    content_height = content.get_height()
    content.set_height(content_height > 200 and 200 or content_height)
    content.set_ellipsize(3) #Omit characters at the end of the text
    self.group.add(content)

    return title.get_height() + content.get_height()

def addBackground(self):
  stageBackground = clutter.Texture('feedimage.png')
  stageBackground.set_position(0, 0)
  self.group.add(stageBackground)

def unescape(s):
  """ Replaces HTML entities with their unicode equivalent"""
  # unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml
  return re.sub('&(%s);' % '|'.join(name2codepoint),
            lambda m: unichr(name2codepoint[m.group(1)]), s)

def remove_html_tags(data):
  """ Removes HTML tags and unscapes the given string. """
  p = re.compile(r'<.*?>')
  return unescape(p.sub('', data))

def main(args=None):
  app = RSSDisplay("http://rss.slashdot.org/Slashdot/slashdot")
  return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))

# Put the ClutterGroup containing all the slide information
# in the top level, so that DDS can get at it.
app = RSSDisplay("http://rss.slashdot.org/Slashdot/slashdot")
#app = RSSDisplay("http://feeds.digg.com/digg/popular.rss")

slide = app.group
