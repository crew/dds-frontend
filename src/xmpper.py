import xmpp
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

def start(slider):
  Thread(target=setupXmpp, args=(slider,)).start()

def createSlideDir(id):
  directory = '%s/%s' % (config.option('cache'), str(id))
  if not os.path.exists(directory):
    os.mkdir(directory)
  return directory

def downloadAsset(asset, slideid, retry=False):
  rootdest = createSlideDir(slideid)
  asseturl = asset['url']
  asseturlpath = urlparse.urlparse(asseturl)[2]
  filename = os.path.basename(asseturlpath)
  destpath = '%s/%s' % (rootdest, filename)
  try:
    urllib.urlretrieve(asseturl, destpath)
    return os.path.exists(destpath)
  except:
    return False

def addSlide(slider, slide):
  logging.info('XMPP addSlide request')
  # slide[0] has a hash with metadata for the slide
  # slide[1] has a list of hashes, where each hash has the url and id of
  # an asset
  def rescheduleAddSlide(slide):
    addSlide(slide)
    return False
  info = slide[0]
  assets = slide[1]
  slideid = info['id']
  directory = createSlideDir(slideid)
  for asset in assets:
    gotasset = downloadAsset(asset, slideid)
    if not gotasset:
      # The asset download failed. What do we do?
      # TODO: reschedule here
      pass
  def trySlideAdd():
    flag = slider.addSlide(info)
    return flag
  gobject.timeout_add(1000, trySlideAdd)

def removeSlide(slider, slide):
  logging.info("XMPP removeSlide request")
  info = slide[0]
  logging.debug('removeslide got info = %s' % str(info))
  slider.removeSlide(info["id"])

def updateSlide(slider, slide):
  logging.info('XMPP updateSlide request')
  logging.debug('Update slide: %s' % str(slide[0]['id']))
  removeSlide(slider, slide)
  addSlide(slider, slide)

def addAsset(slider, slide):
  logging.info("XMPP addAsset request")
  logging.debug('Add Asset: %s' % str(slide))

def removeAsset(slider, slide):
  logging.info("XMPP removeAsset request")
  logging.debug('Remove Asset: %s' % str(slide))

def updateAsset(slider, slide):
  logging.info("XMPP updateAsset request")
  logging.debug('Update Asset: %s' % str(slide))

def handlePresence(dispatch, pr):
  jid = pr.getAttr('from')
  logging.debug('Handle Presence From: %s' % jid)
  dispatch.send(Presence(jid, 'subscribed'))

def checkXmpp(connection):
  try:
    connection.Process(1)
    return True
  except KeyboardInterrupt:
    return False

def proceed(client):
  while checkXmpp(client):
    pass

def setupXmpp(slider):
  jid = config.option("client-jid")
  password = config.option("client-password")
  jid = xmpp.protocol.JID(jid)
  client = xmpp.Client(jid.getDomain(), debug=[])

  if client.connect() == "":
    logging.error("Could not connection to the XMPP server")
    return False

  auth = client.auth(jid.getNode(), password, jid.getResource())
  if not auth:
    logging.error("XMPP password was incorrect")
    return False

  client.RegisterHandler("iq", generateIqHandler(slider))
  client.RegisterHandler("presense", handlePresence)
  client.sendInitPresence()
  client.sendPresence(jid = config.option("server-jid"))
  proceed(client)

def generateIqHandler(slider):
  methods = { "addSlide"    : addSlide,
              "removeSlide" : removeSlide,
              "updateSlide" : updateSlide,
              "addAsset"    : addAsset,
              "removeAsset" : removeAsset,
              "updateAsset" : updateAsset }

  def handleIq(connection, iq):
    if iq.getQueryNS() == xmpp.NS_RPC:
      if iq.getAttr("type") == "error":
        logging.error(iq.getAttr("from"), "rpc error")
      else:
        payload = xmlrpclib.loads(str(iq))
        logging.debug('Payload: %s' % str(payload))
        methodName = payload[1]
        # payload[0] returns a tuple of arguments
        # and the only argument we want is the first one
        if methodName in methods:
          methods[methodName](slider, payload[0])
        else:
          logging.error("rpc function " + methodName +
                        " is not defined")

    raise xmpp.NodeProcessed
  return handleIq
