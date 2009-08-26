#!/usr/bin/python
"""CCIS Crew Digital Display System Frontend/Client

This module is a simple configuration store for key/value pairs.
"""

__author__ = 'CCIS Crew <crew@ccs.neu.edu>'

import ConfigParser
import gflags as flags
import logging
import os
import sys


# Setup command line options for this module
flags.DEFINE_string('config_file', '~/.dds/frontend.cfg',
                    'Configuration file path')
flags.DEFINE_string('config_section', 'DEFAULT',
                    'Configuration file section')
FLAGS = flags.FLAGS

# Old configuration file path
OLD_CONFIG_FILE = os.path.expanduser('~/.dds/config.py')

# Shared options storage
OPTIONS = None


def ConfigFile(filename=None):
  """Get an expanded user path to the configuration file."""
  if not filename:
    filename = FLAGS.config_file
  filename = os.path.expanduser(filename)

  if not os.path.exists(filename):
    logging.error('Could not open config file %s. Please make sure it'
                  ' exists and is readable and try again.\n' % filename)
    sys.exit(1)

  return filename


def Init(file_path=None):
  """Initialize this configuration object.

  Args:
     file_path: (string) full path to configuration file to parse
  """
  global OPTIONS
  file_path = ConfigFile(file_path)
  OPTIONS = ConfigParser.ConfigParser()
  OPTIONS.read(file_path)


def Option(name):
  """Get an option from the configuration object.
  Args:
     name: (string) configuration key
  """
  global OPTIONS
  if OPTIONS is None:
    Init()
  return os.path.expanduser(OPTIONS.get(FLAGS.config_section, name))


def SetOption(name, value):
  """Set an option in the configuration object.
  Args:
     name: (string) configuration key
     value: (string) configuration value
  """
  global OPTIONS
  if OPTIONS is None:
    Init()
  return OPTIONS.set(FLAGS.config_section, name, value)
