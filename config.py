import xml.etree.ElementTree as etree

options = {}

def init(file):
  execfile(file, globals())
  for key in config.keys():
    options[key] = config[key]


def option(name):
  return options[name]

def setOption(name, value):
  options[name] = value
