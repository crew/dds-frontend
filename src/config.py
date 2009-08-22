#!/usr/bin/python
"""Simple Configuration Module for DDS.
"""

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


def config_file():
  """Get an expanded user path to the configuration file."""
  return os.path.expanduser(FLAGS.config_file)


def convert_old():
  """Convert old config.py format to new ConfigParser format."""
  if os.path.exists(OLD_CONFIG_FILE):
    logging.info('Converting old configuration format')
    conf = ConfigParser.ConfigParser()
    if FLAGS.config_section.lower() != 'default':
      conf.add_section(FLAGS.config_section)
    execfile(OLD_CONFIG_FILE, globals())
    for key in config.keys():
      conf.set(FLAGS.config_section, key, config[key])
    conf.write(open(config_file(), 'w'))
    os.rename(OLD_CONFIG_FILE, '%s.old' % OLD_CONFIG_FILE)


def init(file_path=None):
  """Initialize this configuration object.

  Args:
     file_path: (string) full path to configuration file to parse
  """
  convert_old()

  if file_path is None:
    file_path = FLAGS.config_file
  file_path = os.path.expanduser(file_path)

  if not os.path.exists(file_path):
    logging.error('Could not open config file %s. Please make sure it'
                  ' exists and is readable and try again.\n' % file_path)
    sys.exit(1)
  else:
    global OPTIONS
    OPTIONS = ConfigParser.ConfigParser()
    OPTIONS.read(file_path)


def option(name):
  """Get an option from the configuration object.
  Args:
     name: (string) configuration key
  """
  global OPTIONS
  if OPTIONS is None:
    init()
  return os.path.expanduser(OPTIONS.get(FLAGS.config_section, name))


def setOption(name, value):
  """Set an option in the configuration object.
  Args:
     name: (string) configuration key
     value: (string) configuration value
  """
  global OPTIONS
  if OPTIONS is None:
    init()
  return OPTIONS.set(FLAGS.config_section, name, value)
