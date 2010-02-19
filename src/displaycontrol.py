#!/usr/bin/env python
import config
import serial
import logging
import time


class BaseDevice(object):
  def power(self, on=True):
    pass
  def power_on(self):
    self.power(on=True)

  def power_off(self):
    self.power(on=False)

class SerialDevice(BaseDevice):
  def __init__(self, port='/dev/ttyUSB0'):
    BaseDevice.__init__(self)
    self._port = None
    self.port = port

  def serial_port(self):
    if not self._port:
      logging.debug('Connecting to serial port %s' % self.port)
      self._port = serial.Serial(port=self.port)
    return self._port

class SharpAquos(SerialDevice):

  REJECT_POWER_ON = 0
  ACCEPT_POWER_ON = 1

  INPUT_SELECT_TOGGLE = ('ITGD', 1)
  INPUT_SELECT_TV = ('ITVD', 0)
  INPUT_SELECT_IN1 = ('IAVD', 1)
  INPUT_SELECT_IN2 = ('IAVD', 2)
  INPUT_SELECT_IN3 = ('IAVD', 3)
  INPUT_SELECT_IN4 = ('IAVD', 4)
  INPUT_SELECT_IN5 = ('IAVD', 5)
  INPUT_SELECT_IN6 = ('IAVD', 6)
  INPUT_SELECT_IN7 = ('IAVD', 7)

  INPUT_AUTO = '0'
  INPUT_VIDEO = '1'
  INPUT_COMPONENT = '2'

  def _formatcmd(self, cmd, arg):
    cmd = cmd.upper()
    arg = str(arg)
    arglen = len(arg)
    if len(cmd) != 4:
      raise Exception('Aquos commands must be 4 chars in length.')
    if arglen > 4:
      raise Exception('Aquos arguments must be 4 chars in length.')
    elif arglen < 4:
      arg = arg + ' '*(4-arglen)
    return cmd+arg

  def _sendcmd(self, cmd, arg):
    packet = self._formatcmd(cmd, arg)
    logging.debug('Sending %s packet "%s"' % (self.__class__, packet))
    recvbuf = ''
    self.serial_port().write(packet + '\r\n')
    while 'OK' not in recvbuf and 'ERR' not in recvbuf:
      while self.serial_port().inWaiting():
        recvbuf += self.serial_port().read()
    logging.debug('Got "%s" as result of packet %s'
                  % (recvbuf.strip(), packet))
    time.sleep(1)

  def power(self, on=True):
    self._sendcmd('POWR', int(on))

  def widescreen_mode(self, mode):
    self._sendcmd('WIDE', mode)

  def volume(self, val=0):
    assert 0 <= val <= 60
    self._sendcmd('VOLM', '%02d' % val)

  def input_select(self, input):
    assert input in [ self.INPUT_SELECT_TOGGLE, self.INPUT_SELECT_TV,
                      self.INPUT_SELECT_IN1, self.INPUT_SELECT_IN2,
                      self.INPUT_SELECT_IN3, self.INPUT_SELECT_IN4,
                      self.INPUT_SELECT_IN5, self.INPUT_SELECT_IN6,
                      self.INPUT_SELECT_IN7 ]
    self._sendcmd(input[0], input[1])

  def input_select_b(self, input, mode):
    assert input in [ self.INPUT_SELECT_IN1, self.INPUT_SELECT_IN3 ]
    assert mode in [ self.INPUT_AUTO, self.INPUT_VIDEO, self.INPUT_COMPONENT ]
    self.sendcmd('INP'+input[1], mode)
