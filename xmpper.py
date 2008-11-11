import xmpp
from threading import Thread

def create(slider):
    return Xmpper(slider)

class Xmpper(Thread):

    def __init__(self, slider):
        self.slider = slider
        Thread.__init__(self)

    def run(self):
        self.setup_xmpp()

    def got_msg(self, conn, msg):
        print "Sender: " + str(msg.getFrom())
        print "Content: " + str(msg.getBody())
        print msg

    def check_xmpp(self, conn):
        try:
            conn.Process(1)
        except KeyboardInterrupt:
            return 0
        return 1

    def proceed(self, conn):
        while self.check_xmpp(conn):
            pass

    def setup_xmpp(self):
        jid="rms@centipede.ccs.neu.edu"
        pwd="foo"

        jid=xmpp.protocol.JID(jid)
        cl=xmpp.Client(jid.getDomain(), debug=[])

        if cl.connect() == "":
            print "Not Connected!"

        if cl.auth(jid.getNode(), pwd) == None:
            print "Wrong Password Loser"

        cl.RegisterHandler('message', self.got_msg)
        cl.sendInitPresence()

        self.proceed(cl)
