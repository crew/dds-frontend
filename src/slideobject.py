#!/usr/bin/python
"""CCIS Crew Digital Display System Frontend/Client

This module holds the representation of a Slide in memory. Each slide's
metadata is collected here, then parsed and a Clutter Group is
created for the visual representation of a slides content.
"""

__author__ = 'CCIS Crew <crew@ccs.neu.edu>'


import clutter
import config
import gflags
import gobject
import hashlib
import imp
import json
import logging
import os
import sys
import time
import tarfile
import urlparse
import urllib
import thread
import shutil

gflags.DEFINE_boolean('enablescreenshot', False, 'Enable slide screenshots')
gflags.DEFINE_boolean('enableresize', True, 'Enable slide scaling')
gflags.DEFINE_integer('targetwidth', 1920, 'Target screen width')
gflags.DEFINE_integer('targetheight', 1080, 'Target screen height')

FLAGS = gflags.FLAGS

class Slide(object):
  """Class representing all portions of a DDS Slide (metadata and content)."""

  def __init__(self):
    """Create a DDS Slide instance.

    Args:
       filename: (string) path to slide manifest
    """
    self.db_id = None


    # Parsing time limit
    self.timeout = 10

    self.timestamp = None
    self.duration = None
    self.priority = None
    self.transition = None
    self.mode = None
    self.manifestfile = None
    self.manifest = None
    self.dir = None
    # Clutter group representing this slides content
    self.group = None
    # Slide module if python
    self.app = None
    # lock for parsing operations
    self.lock = thread.allocate_lock()
    # gobject event source id of loop event
    self.loop_id = None

  def __repr__(self):
    return str(self)

  def __str__(self):
    if self.manifest and 'title' in self.manifest:
      return '<Slide #%s [%s]>' % (self.id(), self.manifest['title'])
    elif self.id() is not None:
      return '<Slide #%s>' % (self.id())
    else:
      return '<Slide>'

  def __eq__(self, other):
    return (type(self) == type(other)) and (self.id() == other.id())

  @staticmethod
  def create_slide_from_metadata(metadata, width, height):
    """Given slide metadata, create a Slide instance.

    Args:
       metadata: (dictionary) Slide metadata

    Returns:
       Slide instance.

    Note:
       Also creates cached copy of this slide on disk, downloading it's bundle
       and extracting it.
    """
    logging.debug('creating slide from metadata')
    slide = Slide()
    slide.reload(metadata, width, height)
    return slide

  def needs_update(self, metadata):
    needed = self.timestamp != metadata['modified']
    if needed:
      logging.warning('%s needs update per timestamp' % str(self))
    return needed

  def oneslide(self, dir, id=-1):
    """Given slide metadata and a slide, update that slide's information
       and bundle.

    Args:
       metadata: (dictionary) Slide metadata
    """
    logging.debug('creating slide from oneslide')
    self.db_id = id
    self.dir = os.path.expanduser(dir)
    self.parse_directory(self.slide_dir())

  def reload(self, metadata, width, height):
    """Given slide metadata the slide's information and bundle.

    Args:
       metadata: (dictionary) Slide metadata
    """
    if self.lock.locked():
      logging.debug('Failed to reload %s due to lock. Trying again...')
      gobject.timeout_add(5000, lambda: self.reload(metadata, width, height))
      return

    with self.lock:
      logging.debug('reloading %s from metadata' % self)
      self.populate_info(metadata)
      self.retrieve_bundle(metadata['url'], self.slide_dir())
      self.parse_bundle(self.slide_dir(), force=True)
      self.resize(width, height)

  def slide_dir(self):
    """Get the filesystem directory containing this slide data."""
    if self.dir is None:
      self.dir = os.path.join(config.Option('cache'), str(self.id()))
      if not os.path.exists(self.dir):
        os.mkdir(self.dir)
    return self.dir

  def id(self):
    """Returns the Integer ID of this slide."""
    return self.db_id

  def load_slide_id(self, slideid):
    """Given a Slide ID, try and load a cached copy of it from disk.

    Args:
       slideid: (int) Slide ID
    """
    self.db_id = slideid
    self.parse_bundle(self.slide_dir())

  def populate_info(self, metadata):
    """Given a dictionary of slide metadata, update our information.

    Args:
       metadata: (dictionary) Slide metadata
    """
    self.db_id = metadata['id']
    self.timestamp = metadata['modified']

  #TODO(wan): Write the retry code.
  def retrieve_bundle(self, url, directory, unused_retry=False):
    """Download an slide bundle to disk.

    Args:
       url: url to the bundle file.
       directory: the directory to download the bundle to. It'll always be
                  named bundle.tar.gz.
       unused_retry: (Boolean) Should the fetch be retried if it fails
    """
    bundle_path = os.path.join(directory, 'bundle.tar.gz')
    urllib.urlretrieve(url, bundle_path)

  def get_parser_method(self, modename=None):
    """Using self.mode, get the method to use for parsing this slide."""
    parsermap = {'layout': self.parse_json, 'module': self.parse_python}
    if not modename:
      modename = self.mode
    if modename not in parsermap:
      # Should probably be raising an exception here, with some useful
      # information. Otherwise, we'll just get an exception about False
      # not being a callable later on or some shit.
      return False
    return parsermap[modename]

  def get_layout_file(self, modename=None):
    """Using self.mode, get the filename of this slides layout file."""
    layoutfilemap = {'layout': 'layout.js', 'module': 'layout.py'}
    if not modename:
      modename = self.mode
    if modename not in layoutfilemap:
      return False
    return layoutfilemap[modename]

  def extract_bundle(self, directory):
    bundle_path = os.path.join(directory, 'bundle.tar.gz')
    if not os.path.exists(bundle_path):
      logging.error('Bundle path %s does not exist' % bundle_path)
      return False
    bundle = tarfile.open(bundle_path)
    bundle.extractall(directory)
    return True

  def parse_bundle(self, directory, force=False):
    if not self.extract_bundle(directory):
      logging.error('Could not extract bundle for %s in %s' % (self, directory))
      return False
    return self.parse_directory(directory, force)

  def install_fonts(self, directory):
    fonts = self.manifest['fonts']
    if fonts:
      fonts_directory = os.path.expanduser('~/.fonts/')
      if not os.path.exists(fonts_directory):
        os.makedirs(fonts_directory)
      for font_path in fonts:
        shutil.copy(os.path.join(directory, font_path),
          os.path.join(fonts_directory, os.path.basename(font_path)))

  def parse_directory(self, directory, force=False):
    """Parse the bundle in the given directory into self.slide."""
    if self.group and not force:
      return True
    self.manifest = json.load(open(os.path.join(directory, 'manifest.js')))
    self.transition = self.manifest['transition']
    self.mode = self.manifest['mode']
    self.duration = self.manifest['duration']
    self.priority = self.manifest['priority']
    self.install_fonts(directory)
    gobject.timeout_add(1, self.run_parser)
    parsestart = time.time()
    while self.group is None:
      if time.time() - parsestart < self.timeout:
        logging.info('waiting')
        time.sleep(0.8)
      else:
        logging.error('Could not parse fast enough!')
        return False
    self.setupevents()
    return self.group is None

  def run_parser(self):
    """Run the parser for this slide (Executed from a gobject timeout)."""
    parser = self.get_parser_method()
    self.group, self.app = parser(self.get_layout_file(), self.slide_dir())

  def parse_json(self, filename, directory):
    """Parses the given json file into a slide.

    Args:
      filename: (string) json filename
      directory: (string) json directory
      stage: (Clutter Stage) stage to draw layout on

    Returns:
      Parsed slide from setupNewSlide
    """
    filename = os.path.join(directory, filename)
    script = clutter.Script()
    script.add_search_paths(directory)
    script.load_from_file(filename)
    return (script.get_object('slide'), None)

  def parse_python(self, filename, directory):
    """Returns a slide from the given python module.

    Args:
      filename: (string) python module filename
      directory: (string) python module directory
      stage: (Clutter Stage) stage to draw layout on

    Returns:
      Parsed slide from setupNewSlide
    """
    try:
      slidemodule = self.load_module(filename, directory)
      return (slidemodule.slide, slidemodule.app)

    except Exception, e:
      logging.exception('Could not load module %s in dir %s because %s'
                        % (filename, directory, e))

  def load_module(self, codepath, directory):
    """Returns the module object for the python file at the given path.

    Args:
      codepath: (string) filename to load
      directory: (string) directory that filename resides in
    """
    fin = None
    try:
      currentdirectory = os.getcwd()
      currentpath = sys.path
      sys.path.append(directory)
      os.chdir(directory)
      fin = open(codepath, 'rb')
      module = imp.load_source(hashlib.sha1(codepath).hexdigest(), codepath,
                               fin)
      os.chdir(currentdirectory)
      sys.path = currentpath
      return module
    finally:
      if fin:
        fin.close()

  def screenshot_path(self):
    basepath = os.path.join(config.Option('cache'), '..', 'screenshots')
    if not os.path.exists(basepath):
      os.mkdir(basepath)
    return os.path.join(basepath, 'slide-%s.png' % self.id())

  def take_screenshot(self):
    if FLAGS.enablescreenshot and not os.path.exists(self.screenshot_path()):
      gobject.timeout_add(500, self.do_take_screenshot)

  def do_take_screenshot(self):
    logging.info('Taking screenshot')
    os.system("import -window root -silent %s"
              % self.screenshot_path())
    return False

  def resize(self, current_width, current_height):
    if ((current_width == FLAGS.targetwidth) and
        (current_height == FLAGS.targetheight)):
      logging.debug('Skipping resize step, already target size')
    elif not FLAGS.enableresize:
      logging.debug('Skipping resize step, resize disabled')
    else:
      scale_w = float(current_width) / FLAGS.targetwidth
      scale_h = float(current_height) / FLAGS.targetheight
      self.group.set_anchor_point(0, 0)
      self.group.set_scale(scale_w, scale_h)

  def _setupevent(self, event):
      n = 'event_%s' % event
      logging.info('setting up %s in %s' % (n, str(self)))
      if hasattr(self.app, n):
        def callmethod():
          logging.info('Calling %s in %s' % (n, self))
          f = getattr(self.app, n)
          gobject.timeout_add(1, f)
          logging.info('Calling %s in %s complete' % (n, self))
        setattr(self, n,  callmethod)
      elif self.mode == 'module':
        setattr(self, n, lambda: logging.warning('%s undefined in %s'
                                                 % (n, str(self))))
      else:
        ## Doesn't do anything. This is intentional because JSON slides have no
        ## methods
        setattr(self, n, lambda: [])

  def start_event_loop(self):
    if self.loop_id:
       self.stop_event_loop()
    if (self.mode == 'module' and self.manifest and
        'interval' in self.manifest and hasattr(self.app, 'event_loop')):
      logging.info('Starting event loop in %s' % self)
      self.loop_id = gobject.timeout_add(int(self.manifest['interval']),
                                   lambda: self.app.event_loop() or True)

  def stop_event_loop(self):
    if self.loop_id:
      if not gobject.source_remove(self.loop_id):
         logging.error('Failed to remove loop event in %s' % self)
      else:
         logging.info('Stopped event loop in %s' % self)
         self.loop_id = None

  def setupevents(self):
    for x in ['beforeshow', 'aftershow', 'beforehide', 'afterhide']:
      self._setupevent(x)
