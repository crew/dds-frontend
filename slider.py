import config
import glob
import urllib
import time
import clutter
import os.path
import logging
from clutter import Label
from clutter import Texture
from clutter import Group
from clutter import Color
from clutter import EffectTemplate
from clutter import Timeline
from threading import Timer
import xml.sax as sax
from xml.sax.handler import ContentHandler
from xml.sax.handler import ErrorHandler


def create(canvas):
    """Public creator for the slider"""

    return Slider(canvas)

class Slide(Group):

    def __init__(self, transition):
        self.transition = transition
        Group.__init__(self)

class LayoutHandler(ContentHandler):

    def __init__(self, stage, directory):
        self.stage = stage
        self.directory = os.path.expanduser(directory)
        self.locator = None
        self.slide = None
        self.label = None
        self.image = None
        self.video = None

        ContentHandler.__init__(self)

    def setDocumentLocator(self, locator):
        """Set the locator for this document"""

        self.locator = locator

    def startDocument(self):
        """Handle the start of the xml document"""

        pass

    def startElement(self, name, attrs):
        """Handle the start of an xml element"""

        if (self.slide is None) and (name != "slide"):
            #TODO: handle error
            pass

        elif name == "slide":
            transition = attrs.get("transition")
            if transition is None:
                pass
                #TODO: handle error
            self.slide = Slide(transition)

        elif name == "text":
            logging.debug('Adding text element')
            label = Label()
            label.set_font_name(attrs.get("font", "sans 32"))
            label.set_line_wrap(True)
            label.set_color(clutter.color_parse(attrs.get("color", "white")))
            labelWidth = (self.stage.get_width() / 16) * int(attrs.get("width", 16))
            label.set_width(labelWidth)
            labelHeight = (self.stage.get_height() / 9) * int(attrs.get("height", 9))
            label.set_height(labelHeight)
            labelX = (self.stage.get_width() / 16) * int(attrs.get("x", 0))
            label.set_x(labelX)
            labelY = (self.stage.get_height() / 9) * int(attrs.get("y",0))
            label.set_y(labelY)
            label.set_depth(int(attrs.get("z", 0)))
            self.label = label

        elif name == "image":
            logging.debug('Adding image element')
            image = Texture()
            imageWidth = (self.stage.get_width() / 16) * int(attrs.get("width", 16))
            image.set_width(imageWidth)
            imageHeight = (self.stage.get_height() / 9) * int(attrs.get("height", 9))
            image.set_height(imageHeight)
            imageX = (self.stage.get_width() / 16) * int(attrs.get("x", 0))
            image.set_x(imageX)
            imageY = (self.stage.get_height() / 9) * int(attrs.get("y", 0))
            image.set_y(imageY)
            image.set_depth(int(attrs.get("z", 0)))
            self.image = image

        elif name == "video":
            #TODO: implement this
            pass

    def endElement(self, name):

        if name == "text":
            self.slide.add(self.label)
            self.label = None

        if name == "image":
            self.slide.add(self.image)
            self.image = None

        if name == "video":
            #TODO: implement
            pass

    def characters(self, content):

        if not (self.label is None):
            logging.debug('setting text label: %s' % content)
            self.label.set_text(content)

        elif not (self.image is None):
            file = self.directory + "/" + content
            logging.debug('setting image src: %s' % file)
            self.image.set_from_file(file)

        elif not (self.video is None):
            #TODO: implement
            pass


class Slideshow():
    """Slideshow class

    """

    slides = []

    def __init__(self, stage):

        self.stage = stage
        self.current = None
        self.last = None
        self.paint()

    def isEmpty(self):
        return len(self.slides) == 0

    def parseLayout(self, file, directory):
        """Parses the given file into a slide"""
        logging.debug('Parsing layout file: %s dir: %s' % (file, directory))
        handler = LayoutHandler(self.stage, directory)
        sax.parse(file, handler)
        return handler.slide

    def addSlide(self, id, duration, priority, assets, directory):
        logging.debug('Adding New Slide')
        """Add a new slide to the interal cache"""

        slide = self.parseLayout(directory + "/layout.xml", directory)
        slide.___id = id
        slide.duration = duration
        slide.priority = priority
        self.slides.append(slide)
        if not self.current:
            self.current = self.currentSlide()

    def nextSlide(self):
        """Rotate the next slide to the front of the list"""

        self.slides.append(self.slides.pop(0))

    def currentSlide(self):
        """Return the current slide"""

        return self.slides[0]

    def next(self):
        self.load_next()
        self.paint()

    def setup_animation(self):
        logging.debug('Setting up animation')
        if(self.current.transition == "fade"):
            self.current.set_opacity(0)
        elif(self.current.transition == "slide-right-left"):
            self.current.set_x(0 - self.stage.get_width())
        elif(self.current.transition == "slide-left-right"):
            self.current.set_x(self.stage.get_width())
        elif(self.current.transition == "slide-up-down"):
            self.current.set_y(0 - self.stage.get_height())
        elif(self.current.transition == "slide-down-up"):
            self.current.set_y(self.stage.get_height())

    def in_animation(self):
        logging.debug('in animation')
        timeline = clutter.Timeline(fps=60, duration=500)
        template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
        effect = None
        if(self.current.transition == "fade"):
            effect = clutter.effect_fade(template, self.current, 255)
        elif((self.current.transition == "slide-right-left") or
             (self.current.transition == "slide-left-right") or
             (self.current.transition == "slide-up-down") or
             (self.current.transition == "slide-down-up")):
            effect = clutter.effect_move(template, self.current, 0, 0)

        if(effect):
            effect.start()

    def out_animation(self):
        logging.debug('out animation')
        timeline = clutter.Timeline(fps=60, duration=500)
        template = clutter.EffectTemplate(timeline, clutter.sine_inc_func)
        effect = None
        if(self.current.transition == "fade"):
            effect = clutter.effect_fade(template, self.current, 0)
        elif(self.current.transition == "slide-right-left"):
            effect = clutter.effect_move(template, self.current,
                                         self.stage.get_width(), 0)
        elif(self.current.transition == "slide-left-right"):
            effect = clutter.effect_move(template, self.current,
                                         0 - self.stage.get_width(), 0)
        elif(self.current.transition == "slide-up-down"):
            effect = clutter.effect_move(template, self.current,
                                         0, self.stage.get_height())
        elif(self.current.transition == "slide-down-up"):
            effect = clutter.effect_move(template, self.current,
                                         0, 0 - self.stage.get_height())

        if(effect):
            effect.start()

    def load_next(self):
        """Prepare the next slide to be painted"""
        logging.debug('load_next')

        if len(self.slides) > 1:
            self.out_animation()
            if self.last:
                self.last.hide_all()
                self.stage.remove(self.last)
            self.last = self.current
            self.nextSlide()
            self.current = self.currentSlide()
            self.setup_animation()

    def paint(self):
        """Paint the next slide to the screen"""
        logging.debug('paint method begin')
        if self.current:
            logging.debug('painting')
            self.in_animation()
            self.current.show_all()
            self.stage.add(self.current)

class Slider(Slideshow):
    """Manages the order and timing of slide switching"""

    def __init__(self, canvas):
        self.timer = None
        self.active = False
        Slideshow.__init__(self, canvas)

    def start(self):
        """Starts the Slideshow"""
        logging.debug('starting slider')
        self.active = True
        self.setup_animation()
        self.reset_timer()
        self.paint()

    def stop(self):
        """Stops the Slideshow"""
        logging.debug('stopping slider')

        self.active = False
        if self.timer:
            self.timer = None

    def reset_timer(self):
        """Runs the next timer thread to change slides"""

        if self.timer:
            self.timer = None

        if self.active:
            self.timer = Timer(float(self.currentSlide().duration),
                                self.next)
            self.timer.daemon = True
            self.timer.start()

    def next(self):
        """Runs the timer thread for, and shows the next slide"""

        Slideshow.next(self)
        self.reset_timer()
