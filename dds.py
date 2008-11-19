import clutter
import sys
import os
import config
import threading
import time
import gobject
import slider
import xmpper
import logging
from optparse import OptionParser

home = os.environ["HOME"]
configFile = home + "/.dds/config.xml"
logFile = home + "/.dds/log"
cache = None

stage = clutter.stage_get_default()
p = None
## Setup stupid logging for the client
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s', )

def parse_args():
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("-c", "--config", dest="config",
                      help="location of the config file")
    parser.add_option("-l", "--log", dest="log",
                      help="location of the log file")
    parser.add_option("-s", "--slides", dest="slides",
                      help=("location of the slide cache directory "
                            "(overides config file)"))
    (options, args) = parser.parse_args()
    if (options.config):
        configFile = options.config
    if (options.log):
        logFile = options.log
    if (options.slides):
        cache = options.slides

def on_key_press_event(stage, event):
    logging.debug('Got keypress %s' % event.keyval)
    if (event.keyval == 113):
        clutter.main_quit()

def main(args):
    gobject.threads_init()
    clutter.threads_init()
    parse_args()
    config.init(configFile)
    if (cache):
        config.setOption("cache", cache)
    stage.fullscreen()
    stage.set_color(clutter.Color(0x00, 0x00, 0x00, 0x00))
    stage.connect('destroy', clutter.main_quit)
    stage.connect('key-press-event', on_key_press_event)
    stage.hide_cursor()
    stage.show_all()
    show = slider.create(stage)
    p = xmpper.create(show)
    p.setupXmpp()
    p.proceed()
    gobject.timeout_add(5000, p.proceed)
    clutter.main()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
