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

## Setup stupid logging for the client
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s', )

class DDS:
  def __init__(self):
    self._home = os.environ["HOME"]
    self._configFile = self._home + "/.dds/config.xml"
    self._logFile = self._home + "/.dds/log"
    self._cache = None
    self._stage = clutter.stage_get_default()
    self._xmpp = None

  def parse_args(self):
    logging.debug('Parsing Args')
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
      self._configFile = options.config
    if (options.log):
      self._logFile = options.log
    if (options.slides):
      self._cache = options.slides

  def on_key_press_event(self,stage, event):
    logging.debug('Got keypress %s' % event.keyval)
    if (event.keyval == 113):
      clutter.main_quit()
    elif (event.keyval == 65365):
      self._show.next()

  def main(self,args):
    logging.debug('Main method turn on!')
    gobject.threads_init()
    clutter.threads_init()
    self.parse_args()
    config.init(self._configFile)
    if (self._cache):
      config.setOption("cache", cache)
    logging.debug('Going Fullscreen')
    self._stage.fullscreen()
    self._stage.set_color(clutter.Color(0x00, 0x00, 0x00, 0x00))
    self._stage.connect('destroy', clutter.main_quit)
    self._stage.connect('key-press-event', self.on_key_press_event)
    self._stage.hide_cursor()
    self._stage.show_all()
    logging.debug('Creating slider')
    self._show = slider.create(self._stage)
    logging.debug('Creating xmpper')
    self._xmpp = xmpper.create(self._show)
    logging.debug('Starting xmpper')
    self._xmpp.start()
    logging.debug('Clutter Main invocation')
    clutter.main()


if __name__ == '__main__':
  d = DDS()
  retcode = d.main(sys.argv)
  print retcode
  sys.exit(retcode)
