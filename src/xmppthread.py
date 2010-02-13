#!/usr/bin/python
"""CCIS Crew Digital Display System Frontend/Client

This module handles XMPP communication between the frontends and backend.
"""

__author__ = 'CCIS Crew <crew@ccs.neu.edu>'


import xmpp
import xmlrpclib
import logging
import config
import threading
import os

# This should be a list of XMPP resource strings that the server understands.
ALLOWABLERESOURCES = ['dds-client']


class XMPPThread(threading.Thread):
  """Class for interacting with XMPP portions of the DDS System."""

  def __init__(self):
    threading.Thread.__init__(self)

    self.slidemanager = None
    self.connection = None
    self.status = xmpp.Presence()

  def AttachSlideManager(self, slidemanager):
    """Attach a slide manager to this thread.

    Args:
       slidemanager: (SlideManager) slidemanager instance
    """
    self.slidemanager = slidemanager
    self.slidemanager.set_xmpp_handler(self)

  def SetCurrentSlide(self, slide):
    """Send a global presence packet with the current slide ID.

    Args:
       slide: (Slide) Slide object to send out presence for
    """
    # Say hello to the dds-master server with current slideid
    self.status = xmpp.Presence(to=config.Option("server-jid"))
    self.status.setStatus(str(slide.id()))
    self.connection.send(self.status)

  def AddSlide(self, slidetuple):
    """XMPP AddSlide method handler.

    Args:
       slidetuple: (tuple) (slide metadata)
    """
    logging.info('XMPP addSlide request')
    self.slidemanager.add_slide(slidetuple[0])

  def RemoveSlide(self, slidetuple):
    """XMPP RemoveSlide method handler.

    Args:
       slidetuple: (tuple)
    """
    logging.info("XMPP removeSlide request")
    self.slidemanager.remove_slide(slidetuple[0])

  def UpdateSlide(self, slidetuple):
    """XMPP UpdateSlide method handler.

    Args:
       slidetuple: (tuple) (slide metadata)
    """
    logging.info('XMPP updateSlide request')
    self.slidemanager.update_slide(slidetuple[0])

  def GetScreenshot(self, slidetuple):
    logging.warning('STUB: Haven\'t written this code yet. (GetScreenshot)')
    return

#### End XMPP Actions

  def CheckXmpp(self):
    """Checks the XMPP connection to see if it is alive.

    Returns:
       True if connection is alive, False if dead.
    """
    try:
      self.connection.Process(1)
      return True
    except KeyboardInterrupt:
      return False

  def Proceed(self):
    """Call CheckXmpp in a loop, raise an exception if it fails."""
    while self.CheckXmpp():
      pass
    raise Exception('Failed to continue checkXmpp')

  def SetupXmpp(self):
    """Setup the XMPP Connection."""
    jid = config.Option("client-jid")
    password = config.Option("client-password")
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
      logging.warning('Unrecognized XMPP account! Attempting registration')
      ident = {"username": jid.getNode(), "password": password}
      if not xmpp.features.register(self.connection, jid.getDomain(), ident):
        logging.error('XMPP New Account registration failed. Bailing out!')
        os.abort()
        return False
      else:
        # At this point, we have created a new XMPP account, and need to restart
        # the setup process.
        return self.SetupXmpp()

    self.connection.RegisterHandler("iq", self.GenerateIqHandler())
    self.connection.sendInitPresence()

    # Say hello to the dds-master server
    server_jid = xmpp.JID(config.Option("server-jid"))
    self.status = xmpp.Presence(to=server_jid.getStripped())
    self.status.setStatus('initialsliderequest')
    self.connection.send(self.status)

    self.Proceed()

  def GenerateIqHandler(self):
    """Create a function to handle incoming IQ packets."""
    methods = { "addSlide"      : self.AddSlide,
                "removeSlide"   : self.RemoveSlide,
                "updateSlide"   : self.UpdateSlide,
                "getScreenshot" : self.GetScreenshot,
              }

    # pylint: disable-msg=C0103
    def handleIq(unused_connection, iq):
      """Handles incoming IQ packets."""
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

  # pylint: disable-msg=C0103
  def run(self):
    """This method is the 'main' method of the thread."""
    self.SetupXmpp()
