#!/usr/bin/python
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

ALLOWABLERESOURCES = ['dds-client']

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

def scheduleSlideAddition(slider, slideinfo):
  """Try to add a slideinfo dictionary to the slider.

  Args:
     slider: (Slider) slider instance referencing the active slideshow
     slideinfo: (dictionary) slide information as returned from the master
  """
  logging.info('scheduling slide addition for %s' % slideinfo['id'])
  def trySlideAdd():
    flag = slider.addSlide(slideinfo)
    logging.info('Attempting slide add of %s resulted %s'
                 % (slideinfo['id'], flag))
    return flag
  gobject.timeout_add(1000, trySlideAdd)

#### Begin XMPP Methods
def addSlide(slider, slide):
  logging.info('XMPP addSlide request')
  doAddSlide(slider, slide)

def removeSlide(slider, slide):
  logging.info("XMPP removeSlide request")
  doRemoveSlide(slider, slide)

def updateSlide(slider, slide):
  logging.info('XMPP updateSlide request')
  logging.debug('Update slide: %s' % str(slide[0]['id']))
  doUpdateSlide(slider, slide)

def addAsset(slider, slide):
  logging.info("XMPP addAsset request")
  logging.debug('Add Asset: %s' % str(slide))

def removeAsset(slider, slide):
  logging.info("XMPP removeAsset request")
  logging.debug('Remove Asset: %s' % str(slide))

def updateAsset(slider, slide):
  logging.info("XMPP updateAsset request")
  logging.debug('Update Asset: %s' % str(slide))

#### End XMPP Actions

def getSlideAssets(slide):
  slideid = slide[0]['id']
  assets = slide[1]

  logging.info('Starting Asset download for %s' % slideid)
  directory = createSlideDir(slideid)
  for asset in assets:
    gotasset = downloadAsset(asset, slideid)
    if not gotasset:
      # The asset download failed. What do we do?
      # TODO: reschedule here
      logging.warn('Failed to download asset %s' % asset)
  logging.info('Asset download complete for %s' % slideid)

def doAddSlide(slider, slide):
  logging.info('Doing addSlide action')
  # slide[0] has a hash with metadata for the slide
  # slide[1] has a list of hashes, where each hash has the url and id of
  # an asset
  logging.info(slide)

  if len(slide) != 2:
    logging.error('Invalid slide tuple passed: %s' % slide)
    return False

  info = slide[0]
  getSlideAssets(slide) 
  
  scheduleSlideAddition(slider, info)

def doRemoveSlide(slider, slide):
  info = slide[0]
  logging.debug('removeslide got info = %s' % str(info))
  slider.removeSlide(info)

def doUpdateSlide(slider, slide):
  slider.updateSlide(slide[0])
  getSlideAssets(slide)

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
  sys.exit(1)

def setupXmpp(slider):
  jid = config.option("client-jid")
  password = config.option("client-password")
  jid = xmpp.protocol.JID(jid)
  client = xmpp.Client(jid.getDomain(), debug=[])

  if client.connect() == "":
    logging.error("Could not connection to the XMPP server")
    return False

  if jid.getResource() not in ALLOWABLERESOURCES:
    logging.error('Invalid JID Resource given. Must be in: %s'
                  % str(ALLOWABLERESOURCES))
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
