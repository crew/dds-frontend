#!/usr/bin/python
from xmpp import *
import xmlrpclib
import os
import sys
import logging
import config
import urllib
import urlparse
import gobject
import clutter
from threading import Thread

class Xmpper(Thread):
  """Thread to handle talking to the xmpp server, and xmlrpc calls"""

  def __init__(self, slider):
    self.slider = slider
    self.client = None
    self.methods = { "addSlide"   : self.addSlide,
                     "removeSlide" : self.removeSlide,
                     "updateSlide" : self.updateSlide,
                     "addAsset"    : self.addAsset,
                     "removeAsset" : self.removeAsset,
                     "updateAsset" : self.updateAsset }
    Thread.__init__(self)

  def run(self):
    self.setupXmpp()

  def _createSlideDir(self, id):
    directory = '%s/%s' % (config.option('cache'), str(id))
    if not os.path.exists(directory):
      os.mkdir(directory)
    return directory

  def _downloadAsset(self, asset, slideid, retry=False):
    rootdest = self._createSlideDir(slideid)
    asseturl = asset['url']
    asseturlpath = urlparse.urlparse(asseturl)[2]
    filename = os.path.basename(asseturlpath)
    destpath = '%s/%s' % (rootdest, filename)
    try:
      urllib.urlretrieve(asseturl, destpath)
      return os.path.exists(destpath)
    except:
      return False

  def addSlide(self, slide):
    logging.info('XMPP addSlide request')
    #slide[0] has a hash with metadata for the slide
    #slide[1] has a list of hashes, where each hash has the url and id of
    #an asset
    def rescheduleAddSlide(slide):
      self.addSlide(slide)
      return False
    info = slide[0]
    assets = slide[1]
    slideid = info['id']
    directory = self._createSlideDir(slideid)
    for asset in assets:
      gotasset = self._downloadAsset(asset, slideid)
      if not gotasset:
        # The asset download failed. What do we do?
        # TODO: reschedule here
        pass
    def trySlideAdd():
      flag = self.slider.addSlide(info)
      return flag
    gobject.timeout_add(1000, trySlideAdd)

  def removeSlide(self, slide):
    logging.info("XMPP removeSlide request")
    info = slide[0]
    logging.debug('removeslide got info = %s' % str(info))
    self.slider.removeSlide(info["id"])

  def updateSlide(self, slide):
    logging.info('XMPP updateSlide request')
    logging.debug('Update slide: %s' % str(slide[0]['id']))
    self.removeSlide(slide)
    self.addSlide(slide)

  def addAsset(self, slide):
    logging.info("XMPP addAsset request")
    logging.debug('Add Asset: %s' % str(slide))

  def removeAsset(self, slide):
    logging.info("XMPP removeAsset request")
    logging.debug('Remove Asset: %s' % str(slide))

  def updateAsset(self, slide):
    logging.info("XMPP updateAsset request")
    logging.debug('Update Asset: %s' % str(slide))

  def handlePresence(self, dispatch, pr):
    jid = pr.getAttr('from')
    logging.debug('Handle Presence From: %s' % jid)
    dispatch.send(Presence(jid, 'subscribed'))

  def handleIQ(self, connection, iq):
    if iq.getQueryNS() == NS_RPC:
      if iq.getAttr("type") == "error":
        self.logError(iq.getAttr("from"), "rpc error")
      else:
        payload = xmlrpclib.loads(str(iq))
        logging.debug('Payload: %s' % str(payload))
        methodName = payload[1]
        # payload[0] returns a tuple of arguments
        # and the only argument we want is the first one
        if methodName in self.methods:
          self.methods[methodName](payload[0])
        else:
          logging.error("rpc function " + methodName +
                        " is not defined")

    raise NodeProcessed

  def checkXmpp(self, connection):
    try:
      connection.Process(1)
      return True
    except KeyboardInterrupt:
      return False

  def proceed(self):
    while self.checkXmpp(self.client):
      pass

  def setupXmpp(self):
    jid = config.option("client-jid")
    password = config.option("client-password")

    jid = protocol.JID(jid)
    client = Client(jid.getDomain(), debug=[])

    if client.connect() == "":
      logging.error("Could not connection to the XMPP server")

    if client.auth(jid.getNode(), password, jid.getResource()) == None:
      logging.error("XMPP password was incorrect")

    client.RegisterHandler("iq", self.handleIQ)
    client.RegisterHandler("presense", self.handlePresence)
    client.sendInitPresence()
    client.sendPresence(jid = config.option("server-jid"))
    self.client = client
    self.proceed()
