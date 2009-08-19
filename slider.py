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
import xml.etree.ElementTree as etree

def create(canvas):
    """Public creator for the slider"""
    return Slider(canvas)

class Slide(Group):

    def __init__(self):
        transition = None
        duration = None
        Group.__init__(self)

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
            tree = etree.parse(file)
            root = tree.getroot()
            if(root.tag == "slide"):
                self.parseSlide(root);
            else:
                pass

    def parseSlide(self, xml):
        slide = Slide()
        slide.transition = xml.get("transition")
        slide.duration = xml.get("duration")
        #TODO: replace the hardcoded attributes with ones in the xml
        for element in xml.getchildren():
            if(element.tag == "text"):
                label = Label()
                label.set_text(element.text)
                label.set_font_name("sans 32")
                label.set_line_wrap(True)
                label.set_color(Color(0xff, 0xff, 0xff, 0xff))
                label.set_size(self.stage.get_width(),
                               self.stage.get_height())
                slide.add(label);
            elif(element.tag == "image"):
                pass
        self.addSlide(slide)

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
