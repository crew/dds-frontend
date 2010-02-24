#!/usr/bin/env python
import sys
import unittest

sys.path.append("../src")
import gflags as flags

FLAGS = flags.FLAGS


#from slideobject_test import SlideObjectTest
#from xmppthread_test import XMPPThreadTest
from config_test import ConfigTest
from playlist_test import PlaylistTest

if __name__ == '__main__':
    FLAGS(sys.argv)
    unittest.main()
