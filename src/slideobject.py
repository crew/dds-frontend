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
import time
import urlparse
import urllib


class Slide(object):
  """Class representing all portions of a DDS Slide (metadata and content)."""

  def __init__(self, filename=None):
    """Create a DDS Slide instance.

    Args:
       filename: (string) path to slide manifest
    """
    self.PARSER_MAP = {'layout': self.ParseJSON, 'module': self.ParsePython}
    self.LAYOUTFILE_MAP = {'layout': 'layout.js', 'module': 'layout.py'}
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
    s = Slide()
    s.manifest = manifesttuple
    info, assets = s.manifest
    s.UpdateInfo(info)
    s.UpdateAssets(assets)
    s.SaveManifest()
    return s

  def SlideDir(self):
    """Get the filesystem directory containing this slide data."""
    if self.dir is None:
      self.dir = os.path.join(config.option('cache'), str(self.id))
      if not os.path.exists(self.dir):
        os.mkdir(self.dir)
    return self.dir

  def VerifyComplete(self):
    """Verify that we have everything needed to display this slide."""
    ok = True
    if self.mode not in self.LAYOUTFILE_MAP:
      logging.error('Slide ID %s unsupported mode "%s"'
                    % (self.id, self.mode))
      ok = False
    else:
      layoutfilepath = os.path.join(self.SlideDir(),
                                    self.LAYOUTFILE_MAP[self.mode])
      if not os.path.exists(layoutfilepath):
        logging.error('Layout file for slide ID %s missing!' % self.id)
        ok = False

    for asset in self.assets:
      if not self.AssetExists(asset):
        logging.err('Asset missing for slide ID %s: %s' % (slide.id, asset))
        ok = False

    if not ok:
      logging.error('Slide not consistent, missing components.')
      return False
    else:
      return True

  def ParseManifest(self, filename=None, download=True):
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
      self.UpdateInfo(info)
      self.UpdateAssets(assets, download)

  def LoadSlideID(self, id):
    """Given a Slide ID, try and load a cached copy of it from disk.
    
    Args:
       id: (int) Slide ID
    """
    self.id = id
    self.manifestfile = os.path.join(self.SlideDir(), 'manifest.js')
    if not os.path.exists(self.manifestfile):
      raise Exception('Could not find manifest for slide ID: %s' % id)
    else:
      self.ParseManifest(self.manifestfile, download=False)

  def SaveManifest(self):
    """Save the in-memory slide manifest to disk."""
    self.manifestfile = os.path.join(self.SlideDir(), 'manifest.js')
    fh = open(self.manifestfile, 'w')
    json.dump(self.manifest, fh)
    fh.close()

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

  def GetParserMethod(self):
    """Using self.mode, get the method to use for parsing this slide."""
    return self.PARSER_MAP[self.mode]

  def GetLayoutFile(self):
    """Using self.mode, get the filename of this slides layout file."""
    return self.LAYOUTFILE_MAP[self.mode]

  def Parse(self):
    """Parse this slide into self.slide."""
    if self.slide:
      return True

    if not self.VerifyComplete():
      return False
   
    gobject.timeout_add(100, self.RunParser)
    while self.parsedone is None:
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
    self.slide = parser(self.GetLayoutFile(), self.SlideDir())
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
    return script.get_object('slide')

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
      slideModule = self.LoadModule(filename, directory)
      return slideModule.slide
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

  def CanUpdateManifest(self, newmanifest):
    """Given a manifest, determine if it can be used to update this slide.

    Args:
       newmanifest: (tuple) manifest of (slide metadata, assets)
    """
    info, assets = newmanifest
    if info['id'] == self.ID():
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
  def teardownslide(self):
    """Safe alias for self.slide.teardownslide."""
    if hasattr(self.slide, 'teardownslide'):
      self.slide.teardownslide()

  def setupslide(self):
    """Safe alias for self.slide.setupslide."""
    if hasattr(self.slide, 'setupslide'):
      self.slide.setupslide()

