from xmpp import *
import xmlrpclib
import os
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
        #slide[0] has a hash with the id, duration, and priority of the slide
        #slide[1] has a list of hashes, where each hash has the url and id of an asset
        info = slide[0]
        assets = slide[1]
        directory = config.option("cache") + "/" + info["id"]
        if not os.path.exists(directory):
            os.mkdir(directory)
        #for stuff in info.keys():
        for asset in assets:
            opener = urllib.URLopener()
            opener.retrieve(asset["url"], directory)
        info["assets"] = assets
        info["directory"] = directory
        slider.addSlide(**info)
        slider.start()

    def removeSlide(self, slide):
        info = slide[0]
        slider.removeSlide(info["id"])
        if slider.isEmpty(): slider.stop()

    def updateSlide(self, slide):
        print slide
        print "update slide!"

    def addAsset(self, slide):
        print slide
        print "add asset!"

    def removeAsset(self, slide):
        print slide
        print "remove asset!"

    def updateAsset(self, slide):
        print slide
        print "update asset!"

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
        client.sendPresence(jid="test@centipede.ccs.neu.edu/dds-server-init")

        self.proceed(client)
