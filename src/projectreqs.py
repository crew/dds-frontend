#!/usr/bin/python
'''
This simple module tests to see if a module is available for import. If it is not then die, and print a helpful message about what to do
'''

import sys
import logging

def error(msg):
  """Log an error message with the given string then exit.
  Args:
    msg: (string) Error message to log
  """
  logging.error(msg)
  sys.exit(1)

def testit(modulename, errorstr=None):
  """Attempt to import a module, fail if it cannot be loaded.
  Args:
     modulename: (string) Module name to try and import
     errorstr: (string) Display a custom import error instead of a template
  """
  name = modulename.lower()
  if errorstr is None:
    errorstr = ('Python %(name)s module was not found. '
                'apt-get install python-%(name)s' % {'name':name})
  try:
    __import__(modulename)
  except ImportError, e:
    error(errorstr)

# Make sure the following modules are installed. Bail out if not.
testit('clutter')
testit('DNS')
testit('json')
testit('xmpp')
