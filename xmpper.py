from xmpp import *
import xmlrpclib
import os
import os.path

import config
import urllib
import urlparse
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
        #slide[1] has a list of hashes, where each hash has the url and id of
        # an asset
        info = slide[0]
        assets = slide[1]
        configdirectory = config.option("cache") + "/" + str(info["id"])
	directory = os.path.expanduser(configdirectory)
        if not os.path.exists(directory):
            os.mkdir(directory)
        for asset in assets:
            opener = urllib.URLopener()
            path = urlparse.urlparse(asset["url"])[2]
            name = os.path.basename(path)
            place = directory + "/" + name
            opener.retrieve(asset["url"], place)
        info["assets"] = assets
        info["directory"] = directory
        flag = self.slider.isEmpty()
        self.slider.addSlide(**info)
        if flag:
            self.slider.start()

    def removeSlide(self, slide):
        print "REMOVE"
        info = slide[0]
        self.slider.removeSlide(info["id"])
        if self.slider.isEmpty():
            slider.stop()

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
                print payload
                methodName = payload[1]
                # payload[0] returns a tuple of arguments
                # and the only argument we want is the first one
                if methodName in self.methods:
                    self.methods[methodName](payload[0])
                else:
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
        jid = config.option("client-jid")
        password = config.option("client-password")

        jid = protocol.JID(jid)
        client = Client(jid.getDomain(), debug=[])

        if client.connect() == "":
            print "Could not connection to the XMPP server"

        if client.auth(jid.getNode(), password, jid.getResource()) == None:
            print "XMPP password was incorrect"

        client.RegisterHandler("iq", self.handleIQ)
        client.RegisterHandler("presense", self.handlePresence)
        client.sendInitPresence()
        client.sendPresence(jid = config.option("server-jid"))

        self.proceed(client)
