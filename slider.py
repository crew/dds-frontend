import config
import glob
import time
import clutter
from clutter import Label
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

    def __init__(self, duration, transition):
        self.transition = transition
        self.duration = duration
        Group.__init__(self)

class SlideHandler(ContentHandler):

    def __init__(self, stage):
        self.stage = stage
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
            duration = attrs.get("duration")
            transition = attrs.get("transition")
            if duration is None: pass #TODO: handle error
            if transition is None: pass #TODO: handle error
            self.slide = Slide(duration, transition)

        elif name == "text":
            label = Label()
            label.set_font_name(attrs.get("font", "sans 32"))
            label.set_line_wrap(True)
            label.set_color(clutter.color_parse(attrs.get("color", "white")))
            label.set_width(attrs.get("width", self.stage.get_width()))
            label.set_height(attrs.get("height", self.stage.get_height()))
            self.label = label

        elif name == "image":
            #TODO: implement this
            pass

        elif name == "video":
            #TODO: implement this
            pass

    def endElement(self, name):

        if name == "text":
            self.slide.add(self.label)
            self.label = None

        if name == "image":
            #TODO: implement
            pass

        if name == "video":
            #TODO: implement
            pass

    def characters(self, content):

        if not (self.label is None):
            self.label.set_text(content)

        elif not (self.image is None):
            #TODO: implement
            pass

        elif not (self.video is None):
            #TODO: implement
            pass


class Slideshow():
    """Slideshow class

    @param canvas: the canvas to paint on
    """

    slides = []

    def __init__(self, stage):

        self.stage = stage
        self.init()
        self.current = self.currentSlide()
        self.setup_animation()
        self.last = None
        if not len(self.slides) == 0:
            self.paint()

    def init(self):
        """Initializes the cache of slides"""

        files = glob.glob(config.option("cache") + "/*.xml")
        for file in files:
            self.parseSlide(file)
        if len(self.slides) == 0:
            self.active = False
            print "No slides found in the cache"

    def parseSlide(self, file):
        """Parses the given file into a slide"""

        handler = SlideHandler(self.stage)
        sax.parse(file, handler)
        self.addSlide(handler.slide)

    def addSlide(self, slide):
        """Add a new slide to the interal cache"""

        self.slides.append(slide)

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
        if self.current:
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

        self.active = True
        self.reset_timer()

    def stop(self):
        """Stops the Slideshow"""

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
