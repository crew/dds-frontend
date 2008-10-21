import config
import glob
import time
import pgm
from threading import Timer
from pgm.graph.group import Group
from pgm.timing import implicit
import xml.etree.ElementTree as etree

def create(canvas):
    """Public creator for the slider"""
    return Slider(canvas)

class Slideshow(Group):
    """Slideshow class

    @param canvas: the canvas to paint on
    """

    slides = []

    def __init__(self, canvas):

        Group.__init__(self, canvas)
        self.init()
        self._current = pgm.Text(self.currentSlide()["text"])
        self._current.bg_color = (0, 0, 0, 0)
        self._current.height = canvas.height * 0.99
        self._current.width = canvas.width * 0.99
        self._current.font_height = 4/17.0
        self._current.visible = True
        self._current.opacity = 0
        self._last = None
        self._animated = implicit.AnimatedObject(self._current)
        self._animated.setup_next_animations(transformation = implicit.SMOOTH)
        if not len(self.slides) == 0:
            self._paint()

    def init(self):
        """Initializes the cache of slides"""

        files = glob.glob(config.getOption("cache") + "/*.xml")
        for file in files:
            tree = etree.parse(file)
            root = tree.getroot()
            if(root.tag == "slide"):
                slideEntry = {}
                for element in root.getchildren():
                    slideEntry[element.tag] = element.text
                self.addSlide(**slideEntry)
            else:
                pass

    def addSlide(self, title, text, duration):
        """Add a new slide to the interal cache"""

        self.slides.append({"title": title,
                            "text": text,
                            "duration": duration})

    def nextSlide(self):
        """Rotate the next slide to the front of the list"""

        try:
            self.slides.append(self.slides.pop(0))
        except IndexError:
            pass

    def currentSlide(self):
        """Return the current slide"""

        return self.slides[0]

    def next(self):
        self._load_next()
        self._paint()

    #TODO: Document this a bit more
    def _load_next(self):
        """Prepare the next slide to be painted"""

        if len(self.slides) > 1:
            #initialize the fade out
            self._animated.opacity = 0
            if self._last:
                self.remove(self._last)
                del self._last
            self._last = self._current
            self.nextSlide()
            self._current = pgm.Text(self.currentSlide()["text"])
            self._current.visible = True
            self._current.opacity = 0
            self._current.bg_color = (0, 0, 0, 0)
            self._current.position = (0.0, 0.0, 0.0)
            self._current.height = self._canvas.height * 0.99
            self._current.width = self._canvas.width * 0.99
            self._current.font_height = 4/17.0
            #set up the animations for _current
            self._animated = implicit.AnimatedObject(self._current)
            self._animated.setup_next_animations(transformation = implicit.DECELERATE)

    def _paint(self):
        """Paint the next slide to the screen"""

        if self._current:
            #initialize the fade in
            self._animated.opacity = 255
            self.add(self._current)

class Slider(Slideshow):
    """Manages the order and timing of slide switching"""

    def __init__(self, canvas):
        self._timer = None
        self._active = False
        Slideshow.__init__(self, canvas)

    def start(self):
        """Starts the Slideshow"""

        self._active = True
        self.visible = True
        self._timer = Timer(float(self.currentSlide()["duration"]),
                            self.next)
        self._timer.start()

    def stop(self):
        """Stops the Slideshow"""

        self._active = False
        if self._timer:
            self._timer = None

    def _reset_timer(self):
        """Runs the next timer thread to change slides"""

        if self._timer:
            self._timer = None

        if self._active:
            self._timer = Timer(float(self.slides[1]["duration"]),
                                self.next)
            self._timer.daemon = True
            self._timer.start()

    def next(self):
        """Runs the timer thread for, and shows the next slide"""

        self._reset_timer()
        Slideshow.next(self)
