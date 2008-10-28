import pgm
import sys
import os
import config
import threading
import time
import gobject
import slider
from optparse import OptionParser


home = os.environ["HOME"]
configFile = home + "/.dds/config.xml"
logFile = home + "/.dds/log"
cache = None

canvas = pgm.Canvas()
gl = pgm.viewport_factory_make('opengl')
background = pgm.Image()

def parse_args():
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("-c", "--config", dest="config",
                      help="location of the config file")
    parser.add_option("-l", "--log", dest="log",
                      help="location of the log file")
    parser.add_option("-s", "--slides", dest="slides",
                      help="location of the slide cache directory (overides config file)")
    (options, args) = parser.parse_args()
    if(options.config):
        configFile = options.config
    if(options.log):
        logFile = options.log
    if(options.slides):
        cache = options.slides

def on_delete(viewport, event):
    pgm.main_quit()

def on_key_press(viewport, event):
    if event.keyval == pgm.keysyms.q:
        pgm.main_quit()

def main(args):
    gobject.threads_init()
    parse_args()
    config.init(configFile)
    if(cache):
        config.setOption("cache", cache)
    gl.title = 'Crew Digial Display System'
    canvas.size = (16.0, 9.0)
    gl.set_canvas(canvas)
    background.size = canvas.size
    background.bg_color = (45, 45, 45, 255)
    background.show()
    canvas.add(pgm.DRAWABLE_FAR, background)
    gl.connect('delete-event', on_delete)
    gl.connect('key-press-event', on_key_press)
    gl.fullscreen = True
    gl.show()
    show = slider.create(canvas)
    show.start()
    pgm.main()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
