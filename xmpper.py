from xmpp import *
import config
import xml.sax as sax
from xml.sax.handler import ContentHandler
from xml.sax.handler import ErrorHandler
from threading import Thread

def create(slider):
    return Xmpper(slider)


class Xmpper(Thread):

    def __init__(self, slider):
        self.slider = slider
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
        pass

    def removeSlide(self, slide):
        pass

    def updateSlide(self, slide):
        pass

    def addAsset(self, slide):
        pass

    def removeAsset(self, slide):
        pass

    def updateAsset(self, slide):
        pass

    def handlePresence(self, dispatch, pr):
        jid = pr.getAttr('from')
        dispatch.send(Presence(jid, 'subscribed'))

    def handleIQ(self, connection, iq):

        if iq.getQueryNS() == NS_RPC:
            if iq.getAttr("type") == "error":
                self.logError(iq.getAttr("from"), "rpc error")
            else:
                payload = xmlrpclib.loads(str(iq))
                methodName = payload[1]
                # payload[0] returns a tuple of arguments
                # and the only argument we want is the first one
                try:
                    self.methods[methodName](payload[0][0])
                except KeyError:
                    print "rpc function " + methodName + " is not defined"

    def checkXmpp(self, connection):
        try:
            connection.Process(1)
            return True
        except KeyboardInterrupt:
            return False

    def proceed(self, connection):
        while self.checkXmpp(connection):
            pass

    def setupXmpp(self):
        jid = config.option("xmpp-id")
        password = config.option("xmpp-password")

        jid = protocol.JID(jid)
        client = Client(jid.getDomain(), debug=[])

        if client.connect() == "":
            print "Could not connection to the XMPP server"

        if client.auth(jid.getNode(), password) == None:
            print "XMPP password was incorrect"

        client.RegisterHandler("iq", self.handleIQ)
        client.RegisterHandler("presense", self.handlePresence)
        client.sendInitPresence()

        self.proceed(client)
