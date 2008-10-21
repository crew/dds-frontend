import xml.etree.ElementTree as etree

options = {}

def init(file):
    config = etree.parse(file)
    root = config.getroot()
    if(root.tag ==  "config"):
        for element in root.getchildren():
            options[element.get("name")] = element.get("value")
    else:
        raise Exception("Config file isn't valid")

def getOption(name):
    return options[name]

def setOption(name, value):
    options[name] = value
