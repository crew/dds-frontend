#!/usr/bin/python
import os
import sys

options = {}

def init(file):
  if not os.path.exists(file):
    sys.stderr.write('Could not open config file %s. Please make sure it'
                     ' exists and is readable and try again.\n' % file)
    sys.exit(1)
  else:
    execfile(file, globals())
    for key in config.keys():
      options[key] = os.path.expanduser(config[key])


def option(name):
  """
  Get an option from the config db.
  All paths are guaranteed to be expanded.
  """
  return options[name]

def setOption(name, value):
  options[name] = value
