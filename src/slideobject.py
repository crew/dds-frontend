#!/usr/bin/python
"""CCIS Crew Digital Display System Frontend/Client

This module holds the representation of a Slide in memory. Each slide's
metadata is collected here, then parsed and a Clutter Group is
created for the visual representation of a slides content.
"""

__author__ = 'CCIS Crew <crew@ccs.neu.edu>'


import clutter
import config
import gflags as flags
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

flags.DEFINE_boolean('enablescreenshot', False, 'Enable slide screenshots')
FLAGS = flags.FLAGS

class Slide(object):
  """Class representing all portions of a DDS Slide (metadata and content)."""

  def __init__(self):
    """Create a DDS Slide instance.

    Args:
       filename: (string) path to slide manifest
    """
    self.id = None

    # These aren't included in the bundle manifest, so set
    # defaults for testing.
    self.duration = 5
    self.priority = 1

    self.parsedone = None
    self.transition = None
    self.mode = None
    self.manifestfile = None
    self.manifest = None
    self.dir = None
    # Clutter group representing this slides content
    self.slide = None
    # Slide module if python
    self.app = None

  @staticmethod
  def CreateSlideFromMetadata(metadata):
    """Given slide metadata, create a Slide instance.

    Args:
       metadata: (dictionary) Slide metadata

    Returns:
       Slide instance.

    Note:
       Also creates cached copy of this slide on disk, downloading it's bundle
       and extracting it.
    """
    slide = Slide()
    Slide.ReloadSlideFromMetadata(slide, metadata)
    return slide

  @staticmethod
  def ReloadSlideFromMetadata(slide, metadata):
    """Given slide metadata and a slide, update that slide's information
       and bundle.

    Args:
       metadata: (dictionary) Slide metadata
    """
    slide.PopulateInfo(metadata)
    slide.RetreiveBundle(metadata['url'], slide.SlideDir())
    slide.ParseBundle(slide.SlideDir())

  def SlideDir(self):
    """Get the filesystem directory containing this slide data."""
    if self.dir is None:
      self.dir = os.path.join(config.Option('cache'), str(self.ID()))
      if not os.path.exists(self.dir):
        os.mkdir(self.dir)
    return self.dir

  def ID(self):
    """Returns the Integer ID of this slide."""
    return self.id

  def LoadSlideID(self, slideid):
    """Given a Slide ID, try and load a cached copy of it from disk.

    Args:
       slideid: (int) Slide ID
    """
    self.id = slideid
    self.ParseBundle(self.SlideDir())

  def PopulateInfo(self, metadata):
    """Given a dictionary of slide metadata, update our information.

    Args:
       metadata: (dictionary) Slide metadata
    """
    self.id = metadata['id']
    self.duration = metadata['duration']
    self.priority = metadata['priority']

  #TODO(wan): Write the retry code.
  def RetreiveBundle(self, url, directory, unused_retry=False):
    """Download an slide bundle to disk.

    Args:
       url: url to the bundle file.
       directory: the directory to download the bundle to. It'll always be
                  named bundle.tar.gz.
       unused_retry: (Boolean) Should the fetch be retried if it fails
    """
    bundle_path = os.path.join(directory, 'bundle.tar.gz')
    urllib.urlretrieve(url, bundle_path)

  def GetParserMethod(self, modename=None):
    """Using self.mode, get the method to use for parsing this slide."""
    parsermap = {'layout': self.ParseJSON, 'module': self.ParsePython}
    if not modename:
      modename = self.mode
    if modename not in parsermap:
      # Should probably be raising an exception here, with some useful
      # information. Otherwise, we'll just get an exception about False
      # not being a callable later on or some shit.
      return False
    return parsermap[modename]

  def GetLayoutFile(self, modename=None):
    """Using self.mode, get the filename of this slides layout file."""
    layoutfilemap = {'layout': 'layout.js', 'module': 'layout.py'}
    if not modename:
      modename = self.mode
    if modename not in layoutfilemap:
      return False
    return layoutfilemap[modename]

  def ParseBundle(self, directory):
    """Parse the bundle in the given directory into self.slide."""
    if self.slide:
      return True

    bundle_path = os.path.join(directory, 'bundle.tar.gz')
    if not os.path.exists(bundle_path):
      logging.error('Bundle path %s does not exist' % bundle_path)
      return False

    bundle = tarfile.open(bundle_path)
    bundle.extractall(directory)
    fd = open(os.path.join(directory, 'manifest.js'), 'r')
    manifest = json.load(fd)
    self.transition = manifest['transition']
    self.mode = manifest['mode']
    fd.close()
    gobject.idle_add(self.RunParser)
    while not self.parsedone:
      logging.info('waiting')
      time.sleep(0.1)
    return self.parsedone

  def SetParseDone(self, status=True):
    """Set the parse completion status.

    Args:
       stats: (boolean) True/False

    Note:
      Called from gobject.idle_add in runParser
    """
    self.parsedone = status

  def RunParser(self):
    """Run the parser for this slide (Executed from a gobject timeout)."""
    parser = self.GetParserMethod()
    self.slide, self.app = parser(self.GetLayoutFile(), self.SlideDir())
    gobject.idle_add(self.SetParseDone, self.slide is not None)

  def ParseJSON(self, filename, directory):
    """Parses the given json file into a slide.

    Args:
      filename: (string) json filename
      directory: (string) json directory
      stage: (Clutter Stage) stage to draw layout on

    Returns:
      Parsed slide from setupNewSlide
    """
    filename = os.path.join(directory, filename)
    logging.debug('Parsing JSON layout filename: %s' % filename)
    script = clutter.Script()
    script.add_search_paths(directory)
    script.load_from_file(filename)
    return (script.get_object('slide'), None)

  def ParsePython(self, filename, directory):
    """Returns a slide from the given python module.

    Args:
      filename: (string) python module filename
      directory: (string) python module directory
      stage: (Clutter Stage) stage to draw layout on

    Returns:
      Parsed slide from setupNewSlide
    """
    try:
      slidemodule = self.LoadModule(filename, directory)
      return (slidemodule.slide, slidemodule.app)

    except Exception, e:
      logging.error('Could not load module %s in dir %s because %s'
                    % (filename, directory, e))

  def LoadModule(self, codepath, directory):
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
      module = imp.load_source(hashlib.sha1(codepath).hexdigest(),
                               codepath, fin)
      os.chdir(currentdirectory)
      sys.path = currentpath
      return module
    finally:
      if fin:
        fin.close()

  ## Following two methods virtual as they call a method if present on
  ## self.slide
  # pylint: disable-msg=C0103
  def teardownslide(self):
    """Safe alias for self.slide.teardownslide."""
    if hasattr(self.slide, 'teardownslide'):
      self.slide.teardownslide()

  # pylint: disable-msg=C0103
  def setupslide(self):
    """Safe alias for self.slide.setupslide."""
    if hasattr(self.app, 'setupslide'):
      self.app.setupslide()

  def ScreenshotPath(self):
    basepath = os.path.join(config.Option('cache'), '..', 'screenshots')
    if not os.path.exists(basepath):
      os.mkdir(basepath)
    return os.path.join(basepath, 'slide-%s.png' % self.ID())

  def TakeScreenshot(self):
    if FLAGS.enablescreenshot and not os.path.exists(self.ScreenshotPath()):
      gobject.timeout_add(500, self.DoTakeScreenshot)

  def DoTakeScreenshot(self):
    logging.info('Taking screenshot')
    os.system("import -window root -silent %s"
              % self.ScreenshotPath())
    return False


