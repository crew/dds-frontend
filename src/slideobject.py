#!/usr/bin/python
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
import urlparse
import urllib

class UnsupportedSlideModeException(Exception):
  """Raised when one tries to parse an unsupported slide mode."""
  pass

class Slide(object):

  def __init__(self, filename=None):
    """Create a DDS Slide instance.

    Args:
       filename: (string) path to slide manifest
    """
    self.PARSER_MAP = {'layout': self.parseJSON, 'module': self.parsePython}
    self.LAYOUTFILE_MAP = {'layout': 'layout.js', 'module': 'layout.py'}
    self.id = None
    self.duration = None
    self.transition = None
    self.mode = None
    self.priority = None

    self.info = None
    self.assets = None

    self.manifestfile = None
    self.manifest = None
    self.dir = None
    # Clutter group representing this slides content
    self.slide = None

    if filename is not None:
      self.parseManifest(filename)

  @staticmethod
  def CreateSlideWithManifest(manifesttuple):
    s = Slide()
    s.manifest = manifesttuple
    info, assets = s.manifest
    logging.info('Creating new slide from tuple')
    logging.info('info: %s' % str(info))
    logging.info('assets: %s' % str(assets))
    s.updateInfo(info)
    s.updateAssets(assets)
    s.saveManifest()
    return s

  def slideDir(self):
    if self.dir is None:
      self.dir = os.path.join(config.option('cache'), str(self.id))
      if not os.path.exists(self.dir):
        os.mkdir(self.dir)
    return self.dir

  def verifyComplete(self):
    ok = True
    layoutfilepath = os.path.join(self.slideDir(),
                                  self.LAYOUTFILE_MAP[self.mode])
    if not os.path.exists(layoutfilepath):
      logging.error('Layout file for slide ID %s missing!' % self.id)
      ok = False

    for asset in self.assets:
      if not self.assetExists(asset):
        logging.err('Asset missing for slide ID %s: %s' % (slide.id, asset))
        ok = False

    if not ok:
      logging.error('Slide not consistent, missing components.')
      return False
    else:
      return True

  def parseManifest(self, filename=None):
    """Parse a JSON slide manifest.

    Args:
       filename: (string) path to slide manifest
    """
    if filename:
      self.manifestfile = filename
      fh = open(self.manifestfile, 'r')
      self.manifest = json.load(fh)
      fh.close()

    if self.manifest:
      info, assets = self.manifest
      self.updateInfo(info)
      self.updateAssets(assets)

  def saveManifest(self):
    self.manifestfile = os.path.join(self.slideDir(), 'manifest.js')
    fh = open(self.manifestfile, 'w')
    json.dump(self.manifest, fh)
    fh.close()

  def updateInfo(self, infohash):
    self.info = infohash
    self.id = self.info['id']
    self.duration = self.info['duration']
    self.transition = self.info['transition']
    self.mode = self.info['mode']
    self.priority = self.info['priority']

  def updateAssets(self, assetlist):
    self.assets = assetlist
    for asset in self.assets:
      self.downloadAsset(asset)

  def assetFilePath(self, asset):
    asseturl = asset['url']
    asseturlpath = urlparse.urlparse(asseturl)[2]
    filename = os.path.basename(asseturlpath)
    return os.path.join(self.slideDir(), filename)

  def assetExists(self, asset):
    return os.path.exists(self.assetFilePath(asset))

  def downloadAsset(self, asset, retry=False):
    asseturl = asset['url']
    destpath = self.assetFilePath(asset)
    urllib.urlretrieve(asseturl, destpath)
    return self.assetExists(asset)

  def parse(self):
    if self.mode not in self.PARSER_MAP:
      raise UnsupportedSlideModeException
    
    self.slide = self.PARSER_MAP[self.mode](self.LAYOUTFILE_MAP[self.mode],
                                            self.slideDir())

  def parseJSON(self, filename, directory):
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
    return script.get_object('slide')

  def parsePython(self, filename, directory):
    """Returns a slide from the given python module.

    Args:
      filename: (string) python module filename
      directory: (string) python module directory
      stage: (Clutter Stage) stage to draw layout on

    Returns:
      Parsed slide from setupNewSlide
    """
    try:
      slideModule = self.loadModule(filename, directory)
      return slideModule.slide
    except Exception, e:
      logging.error('Could not load module %s in dir %s because %s'
                    % (filename, directory, e))

  def loadModule(self, codepath, directory):
    """Returns the module object for the python file at the given path.

    Args:
      codepath: (string) filename to load
      directory: (string) directory that filename resides in
    """
    fin = None
    try:
      currentDirectory = os.getcwd()
      currentPath = sys.path
      sys.path.append(directory)
      os.chdir(directory)
      fin = open(codepath, 'rb')
      module = imp.load_source(hashlib.sha1(codepath).hexdigest(),
                               codepath, fin)
      os.chdir(currentDirectory)
      sys.path = currentPath
      return module
    finally:
      if fin:
        fin.close()

  def attach(self, slidemanager):
    """Attach this slide to a slidemanager.

    Args:
       slidemanager: (SlideManager) Deck this slide will be inserted into.
    """
    logging.info('self.slide: %s' % self.slide)
    logging.info('Called attach with manager: %s' % slidemanager)
    slidemanager.addSlide(self)

  def teardownslide(self):
    if hasattr(self.slide, 'teardownslide'):
      self.slide.teardownslide()

  def setupslide(self):
    if hasattr(self.slide, 'setupslide'):
      self.slide.setupslide()

  def canUpdateManifest(self, newmanifest):
    info, assets = newmanifest
    if info['id'] == self.id:
      return True
    return False

  def updateManifest(self, newmanifest):
    self.manifest = newmanifest
    self.saveManifest()
    self.parseManifest()