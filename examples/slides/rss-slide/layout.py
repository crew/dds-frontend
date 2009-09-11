import clutter, gtk.gdk
import sys
import feedparser
# regex lib for stripping HTML tags
import re

# This class displays a single entry (the latest) in an RSS feed.
# it is strictly static content at the moment - however, this
# class is intended to be a template to easily incorperate ANY RSS
# feed into DDS, simply by initializing it with a different feed.
class RSSDisplay(object):
  def __init__(self, feedURL):
    """ Initializes the stage and score for this slide. """
    self.group = clutter.Group()
    self.group.set_size(1920, 1080)
    self.addrss(feedURL)
    self.group.setupslide = lambda: self.refresh(feedURL)
    # self.addBackground()

  def refresh(self, feedURL):
    self.group.remove_all()
    self.addrss(feedURL)

  def addrss(self, feedURL):
    """ Adds the RSS feed information to this slide. """
    #TODO: ERROR CHECKING: MAKE SURE WE DON'T EXPLODE WITH A BAD FEED
    rssfeed = feedparser.parse(feedURL)
    feedtitle = remove_html_tags(rssfeed.feed.title)
    feedtitleActor = clutter.label_new_with_text("serif 36", feedtitle)
    feedtitleActor.set_color(clutter.color_parse("gold"))
    feedtitleActor.set_size(1920, 100)
    feedtitleActor.set_position(0, 0)
    self.group.add(feedtitleActor)

    y = 100
    for entry in rssfeed.entries:
      y += self.add_entry_group(entry, y, width=1920) + 20

  def add_entry_group(self, entry, starty, width=1920):
    topstorytitle = remove_html_tags(entry.title)
    title = clutter.label_new_with_text("serif 32", topstorytitle)
    title.set_width(width)
#size(1920, 100)
    title.set_color(clutter.color_parse("white"))
    title.set_position(0, starty)
    self.group.add(title)

    topstorytext = remove_html_tags(entry.summary)
    content = clutter.label_new_with_text("serif 24", "test")
    content.set_line_wrap(True)
    content.set_line_wrap_mode(2)
    content.set_color(clutter.color_parse("white"))
    content.set_position(0, starty + title.get_height())
#    content.set_size(1920, 200)
    content.set_width(width)
    content.set_text(topstorytext)
    content.set_clip(0, 0, 1920, 200)
    self.group.add(content)

    content_height = content.get_height()
    return title.get_height() + content_height > 200 and 200 or content_height

  def addBackground(self):
    stageBackground = clutter.Texture('feedimage.png')
    stageBackground.set_position(0, 0)
    self.group.add(stageBackground)


def remove_html_tags(data):
  """ Removes HTML tags from a given string. """
  p = re.compile(r'<.*?>')
  return p.sub('', data)

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
