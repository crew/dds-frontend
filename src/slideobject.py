#!/usr/bin/python
"""CCIS Crew Digital Display System Frontend/Client

This module holds the representation of a Slide in memory. Each slide's
metadata and assets are collected here, then parsed and a Clutter Group is
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
import urlparse
import urllib

FLAGS = flags.FLAGS

class Slide(object):
  """Class representing all portions of a DDS Slide (metadata and content)."""

  def __init__(self, filename=None):
    """Create a DDS Slide instance.

    Args:
       filename: (string) path to slide manifest
    """
    self.id = None
    self.duration = None
    self.transition = None
    self.mode = None
    self.priority = None
    self.parsedone = None

    self.info = None
    self.assets = None

    self.manifestfile = None
    self.manifest = None
    self.dir = None
    # Clutter group representing this slides content
    self.slide = None
    # Slide module if python
    self.app = None

    if filename is not None:
      self.ParseManifest(filename)

  @staticmethod
  def CreateSlideWithManifest(manifesttuple):
    """Given a slide manifest, create a Slide instance.

    Args:
       manifesttuple: (tuple) contains (slide metadata, assetlist)

    Returns:
       Slide instance.

    Note:
       Also creates cached copy of this slide on disk, and downloads all the
       needed assets.
    """
    slide = Slide()
    slide.manifest = manifesttuple
    info, assets = slide.manifest
    slide.UpdateInfo(info)
    slide.UpdateAssets(assets)
    slide.SaveManifest()
    return slide

  def SlideDir(self):
    """Get the filesystem directory containing this slide data."""
    if self.dir is None:
      self.dir = os.path.join(config.Option('cache'), str(self.ID()))
      if not os.path.exists(self.dir):
        os.mkdir(self.dir)
    return self.dir

  def VerifyComplete(self):
    """Verify that we have everything needed to display this slide."""
    complete = True
    if not self.GetLayoutFile():
      logging.error('Slide ID %s unsupported mode "%s"'
                    % (self.ID(), self.mode))
      complete = False
    else:
      layoutfilepath = os.path.join(self.SlideDir(), self.GetLayoutFile())
      if not os.path.exists(layoutfilepath):
        logging.error('Layout file for slide ID %s missing!' % self.ID())
        complete = False

    for asset in self.assets:
      if not self.AssetExists(asset):
        logging.error('Asset missing for slide ID %s: %s' % (self.ID(), asset))
        complete = False

    if not complete:
      logging.error('Slide not consistent, missing components.')
      return False
    else:
      return True

  def ParseManifest(self, filename=None, download=False):
    """Parse a JSON slide manifest.

    Args:
       filename: (string) path to slide manifest
    """
    if filename:
      self.manifestfile = filename
      filehandle = open(self.manifestfile, 'r')
      self.manifest = json.load(filehandle)
      filehandle.close()

    if self.manifest:
      info, assets = self.manifest
      self.UpdateInfo(info)
      self.UpdateAssets(assets, download)

  def LoadSlideID(self, slideid):
    """Given a Slide ID, try and load a cached copy of it from disk.
    
    Args:
       slideid: (int) Slide ID
    """
    self.id = slideid
    self.manifestfile = os.path.join(self.SlideDir(), 'manifest.js')
    if not os.path.exists(self.manifestfile):
      raise Exception('Could not find manifest for slide ID: %s' % self.ID())
    else:
      self.ParseManifest(self.manifestfile, download=False)

  def SaveManifest(self):
    """Save the in-memory slide manifest to disk."""
    self.manifestfile = os.path.join(self.SlideDir(), 'manifest.js')
    filehandle = open(self.manifestfile, 'w')
    json.dump(self.manifest, filehandle)
    filehandle.close()

  def UpdateInfo(self, infohash):
    """Given a dictionary of slide metadata, update our saved copy.

    Args:
       infohash: (dictionary) Slide metadata
    """
    self.info = infohash
    self.id = self.info['id']
    self.duration = self.info['duration']
    self.transition = self.info['transition']
    self.mode = self.info['mode']
    self.priority = self.info['priority']

  def UpdateAssets(self, assetlist, download=True):
    """Given a list of assets, update our saved assetlist.

    Args:
       assetlist: (list of dict) Contains a list of this slides assets
       download: (boolean) If true, download the assets to disk.
    """
    self.assets = assetlist
    if download:
      for asset in self.assets:
        self.DownloadAsset(asset)

  def AssetFilePath(self, asset):
    """Get the final filesystem path of a given asset.

    Args:
       asset: (dictionary) information about the asset to be downloaded
    """
    asseturl = asset['url']
    asseturlpath = urlparse.urlparse(asseturl)[2]
    filename = os.path.basename(asseturlpath)
    return os.path.join(self.SlideDir(), filename)

  def AssetExists(self, asset):
    """Get a boolean answer to the question of if an asset exists on disk."""
    return os.path.exists(self.AssetFilePath(asset))

  #TODO(wan): Write the retry code.
  def DownloadAsset(self, asset, unused_retry=False):
    """Download an Asset to Disk.

    Args:
       asset: (dictionary) information about the asset to be downloaded
       unused_retry: (Boolean) Should the fetch be retried if it fails
    """
    asseturl = asset['url']
    destpath = self.AssetFilePath(asset)
    urllib.urlretrieve(asseturl, destpath)
    return self.AssetExists(asset)

  def GetParserMethod(self, modename=None):
    """Using self.mode, get the method to use for parsing this slide."""
    parsermap = {'layout': self.ParseJSON, 'module': self.ParsePython}
    if not modename:
      modename = self.mode
    if modename not in parsermap:
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

  def Parse(self):
    """Parse this slide into self.slide."""
    if self.slide:
      return True

    if not self.VerifyComplete():
      return False
  
    gobject.idle_add(self.RunParser)
    while not self.parsedone:
      logging.info('waiting')
      time.sleep(0.1)
    return self.parsedone
    
  def SetParseDone(self, status=True):
    """Set the parse completion status.
    
    Args:
       stats: (boolean) True/False i

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

  def CanUpdateManifest(self, newmanifest):
    """Given a manifest, determine if it can be used to update this slide.

    Args:
       newmanifest: (tuple) manifest of (slide metadata, assets)
    """
    if newmanifest[0]['id'] == self.ID():
      return True
    return False

  def UpdateManifest(self, newmanifest):
    """Given a manifest, update our stored copy and re-parse.

    Args:
       newmanifest: (tuple) manifest of (slide metadata, assets)
    """
    self.manifest = newmanifest
    self.SaveManifest()
    self.ParseManifest()

  def ID(self):
    """Returns the Integer ID of this slide."""
    return self.id

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
    if hasattr(self.slide, 'setupslide'):
      self.slide.setupslide()

  def ScreenshotPath(self):
    basepath = os.path.join(config.Option('cache'), '..', 'screenshots')
    if not os.path.exists(basepath):
      os.mkdir(basepath)
    return os.path.join(basepath, 'slide-%s.png' % self.ID())

  def TakeScreenshot(self):
    if not os.path.exists(self.ScreenshotPath()):
      gobject.timeout_add(500, self.DoTakeScreenshot)

  def DoTakeScreenshot(self):
    logging.info('Taking screenshot')
    os.system("import -window root -silent %s"
              % self.ScreenshotPath())
    return False


