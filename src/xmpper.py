#!/usr/bin/python
from xmpp import *
import xmlrpclib
import os
import os.path
import sys
import logging
import config
import urllib
import urlparse
import gobject
import clutter
import xml.sax as sax
from xml.sax.handler import ContentHandler
from xml.sax.handler import ErrorHandler
from threading import Thread

def create(slider):
  return Xmpper(slider)

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

  def addSlide(self, slide):
    logging.debug('XMPP addSlide request')
    #slide[0] has a hash with the id, duration, and priority of the slide
    #slide[1] has a list of hashes, where each hash has the url and id of
    #an asset
    info = slide[0]
    assets = slide[1]
    configdirectory = config.option("cache") + "/" + str(info["id"])
    directory = os.path.expanduser(configdirectory)
    if not os.path.exists(directory):
      os.mkdir(directory)
    for asset in assets:
      path = urlparse.urlparse(asset["url"])[2]
      name = os.path.basename(path)
      fullPath = directory + "/" + name
      urllib.urlretrieve(asset["url"], fullPath)
    info["assets"] = assets
    info["directory"] = directory
    flag = self.slider.isEmpty()
    def callback(info):
      clutter.threads_enter()
      flag = self.slider.addSlide(**info)
      clutter.threads_leave()
      return flag
    gobject.timeout_add(1000, callback, info)

  def removeSlide(self, slide):
    logging.debug("removing a slide")
    info = slide[0]
    logging.debug('removeslide got info = %s' % str(info))
    try:
      self.slider.removeSlide(info)
    except:
      logging.debug('Removeslide died again. FIXME!!!!!!!!!!!!!!!!!!')
      logging.debug(str(sys.exc_info()))
    if self.slider.isEmpty():
      slider.stop()

  def updateSlide(self, slide):
    logging.debug('Update slide: %s' % str(slide[0]['id']))
    self.removeSlide(slide)
    self.addSlide(slide)

  def addAsset(self, slide):
    logging.debug('Add Asset: %s' % str(slide))

  def removeAsset(self, slide):
    logging.debug('Remove Asset: %s' % str(slide))

  def updateAsset(self, slide):
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
      # This is kind of stupid debugging
      #logging.debug("checkXmpp: Connection Processed")
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
