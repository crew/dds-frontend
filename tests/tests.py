#!/usr/bin/env python
import sys
sys.path.append("../src")
import gflags as flags

FLAGS = flags.FLAGS

from slider_test import SliderTest
import unittest

if __name__ == '__main__':
    FLAGS(sys.argv)
    unittest.main()
