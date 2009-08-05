#!/usr/bin/python
"""Simple Configuration Module for DDS.
"""

import gflags as flags
import os
import sys


# Setup command line options for this module
flags.DEFINE_string('config_file', '~/.dds/config.py',
                    'Configuration file path')
FLAGS = flags.FLAGS

# Shared options storage
OPTIONS = {}

def init(file_path=None):

  if file_path is None:
    file_path = FLAGS.config_file
  file_path = os.path.expanduser(file_path)

  if not os.path.exists(file_path):
    sys.stderr.write('Could not open config file %s. Please make sure it'
                     ' exists and is readable and try again.\n' % file)
    sys.exit(1)
  else:
    execfile(file_path, globals())
    for key in config.keys():
      OPTIONS[key] = os.path.expanduser(config[key])


def option(name):
  """
  Get an option from the config db.
  All paths are guaranteed to be expanded.
  """
  return OPTIONS[name]

def setOption(name, value):
  OPTIONS[name] = value
