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


class XMPPThread(threading.Thread):
  """Class for interacting with XMPP portions of the DDS System."""

  def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
    threading.Thread.__init__(self, group, target, name, args, kwargs)

    self.slidemanager = None
    self.status = xmpp.Presence()

  def AttachSlideManager(self, slidemanager):
    """Attach a slide manager to this thread.
    
    Args:
       slidemanager: (SlideManager) slidemanager instance
    """
    self.slidemanager = slidemanager
    self.slidemanager.SetXMPPHandler(self)

  def SetCurrentSlide(self, slide):
    """Send a global presence packet with the current slide ID.

    Args:
       slide: (Slide) Slide object to send out presence for
    """
    self.status.setStatus('Current=%s' % slide.ID())
    self.connection.send(self.status)

  def AddSlide(self, slidetuple):
    """XMPP addSlide method handler.

    Args:
       slidetuple: (tuple) (slide metadata, slide assets)
    """
    logging.info('XMPP addSlide request')
    if len(slidetuple) != 2:
      logging.error('Invalid slide tuple passed: %s' % slidetuple)
      return False

    self.slidemanager.AddSlide(slidetuple)

  def RemoveSlide(self, slidetuple):
    """XMPP removeSlide method handler.

    Args:
       slidetuple: (tuple)
    """
    logging.info("XMPP removeSlide request")
    info = slidetuple[0]
    logging.debug('removeslide got info = %s' % str(info))
    self.slidemanager.RemoveSlide(info)

  def UpdateSlide(self, slidetuple):
    logging.info('XMPP updateSlide request')
    logging.debug('Update slide: %s' % str(slidetuple[0]['id']))
    self.slidemanager.UpdateSlide(slidetuple)

#### End XMPP Actions

  def CheckXmpp(self):
    try:
      self.connection.Process(1)
      return True
    except KeyboardInterrupt:
      return False

  def Proceed(self):
    while self.CheckXmpp():
      pass
    raise Exception('Failed to continue checkXmpp')

  def SetupXmpp(self):
    jid = config.option("client-jid")
    password = config.option("client-password")
    jid = xmpp.protocol.JID(jid)
    self.connection = xmpp.Client(jid.getDomain(), debug=[])

    if self.connection.connect() == "":
      logging.error("Could not connection to the XMPP server")
      return False

    if jid.getResource() not in ALLOWABLERESOURCES:
      logging.error('Invalid JID Resource given. Must be in: %s'
                    % str(ALLOWABLERESOURCES))
      return False
    auth = self.connection.auth(jid.getNode(), password, jid.getResource())
    if not auth:
      logging.error("XMPP password was incorrect")
      return False

    self.connection.RegisterHandler("iq", self.GenerateIqHandler())
    self.connection.sendInitPresence()
    p = xmpp.Presence(to=config.option("server-jid"))
    p.setStatus('initialsliderequest')
    self.connection.send(p)
    self.Proceed()

  def GenerateIqHandler(self):
    methods = { "addSlide"    : self.AddSlide,
                "removeSlide" : self.RemoveSlide,
                "updateSlide" : self.UpdateSlide,
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
            methods[methodName](payload[0])
          else:
            logging.error("rpc function " + methodName +
                          " is not defined")

      raise xmpp.NodeProcessed
    return handleIq

  ## Lowercase method name to override threading.Thread
  def run(self):
    self.SetupXmpp()
