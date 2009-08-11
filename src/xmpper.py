#!/usr/bin/python
import xmpp
import xmlrpclib
import os
import sys
import json
import logging
import config
import urllib
import urlparse
import gobject
import clutter
import threading

ALLOWABLERESOURCES = ['dds-client']

def start(slider):
  threading.Thread(target=setupXmpp, args=(slider,)).start()

#### Begin XMPP Methods
def addSlide(slider, slidetuple):
  logging.info('XMPP addSlide request')
  if len(slidetuple) != 2:
    logging.error('Invalid slide tuple passed: %s' % slidetuple)
    return False

  # We have to wrap slide creation in a gobject timeout. Slide parsing (clutter
  # object creation) doesn't like happening in a different thread (this method
  # will get called from the XMPP thread)
  gobject.timeout_add(100, slider.addSlide, slidetuple)

def removeSlide(slider, slidetuple):
  logging.info("XMPP removeSlide request")
  info = slidetuple[0]
  logging.debug('removeslide got info = %s' % str(info))
  slider.removeSlide(info)

def updateSlide(slider, slidetuple):
  logging.info('XMPP updateSlide request')
  logging.debug('Update slide: %s' % str(slidetuple[0]['id']))
  slider.updateSlide(slidetuple)

#### End XMPP Actions

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
            }

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
