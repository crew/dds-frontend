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

  MUTE_TOGGLE = 0
  MUTE_ON = 1
  MUTE_OFF = 2

  SURROUND_TOGGLE = 0
  SURROUND_ON = 1
  SURROUND_OFF = 2

  WIDE_TOGGLE_AV = 0
  WIDE_SIDEBAR_AV = 1
  WIDE_SSTRETCH_AV = 2
  WIDE_ZOOM_AV = 3
  WIDE_STRETCH_AV = 4
  WIDE_NORMAL_PC = 5
  WIDE_ZOOM_PC = 6
  WIDE_STRETCH_PC = 7
  WIDE_DOT_BY_DOT = 8
  WIDE_FULLSCREEN_AV = 9

  SLEEP_OFF = 0
  SLEEP_30M = 1
  SLEEP_60M = 2
  SLEEP_90M = 3
  SLEEP_120M = 4

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
    return self._sendcmd('POWR', int(on))

  def restrict_power(self, on=False):
    return self._sendcmd('RSPW', int(not on))

  def widescreen_mode(self, mode):
    #FIXME
    assert mode in [ self.WIDE_DOT_BY_DOT ]
    return self._sendcmd('WIDE', mode)

  def volume(self, val=0):
    assert 0 <= val <= 60
    return self._sendcmd('VOLM', '%02d' % val)

  def input_select(self, input):
    assert input in [ self.INPUT_SELECT_TOGGLE, self.INPUT_SELECT_TV,
                      self.INPUT_SELECT_IN1, self.INPUT_SELECT_IN2,
                      self.INPUT_SELECT_IN3, self.INPUT_SELECT_IN4,
                      self.INPUT_SELECT_IN5, self.INPUT_SELECT_IN6,
                      self.INPUT_SELECT_IN7 ]
    return self._sendcmd(input[0], input[1])

  def input_select_b(self, input, mode):
    assert input in [ self.INPUT_SELECT_IN1, self.INPUT_SELECT_IN3 ]
    assert mode in [ self.INPUT_AUTO, self.INPUT_VIDEO, self.INPUT_COMPONENT ]
    return self._sendcmd('INP'+input[1], mode)

  def mute(self, mode):
    assert mode in [ self.MUTE_TOGGLE, self.MUTE_ON, self.MUTE_OFF ]
    return self._sendcmd('MUTE', mode)

  def surround(self, mode):
    assert mode in [ self.SURROUND_TOGGLE, self.SURROUND_ON,
                     self.SURROUND_OFF ]
    return self._sendcmd('ACSU', mode)

  def audio_selection(self):
    """Toggle audio selection"""
    return self._sendcmd('ACHA', 0)

  def closed_caption(self):
    """Toggle CC selection"""
    return self._sendcmd('CLCP', 0)

  def channel_up(self):
    return self._sendcmd('CHUP', 0)

  def channel_down(self):
    return self._sendcmd('CHDW', 0)

  def ota_digital_channel(self, prefix, suffix):
    prefix, suffix = map(int, [prefix, suffix])
    assert 1 <= prefix <= 99
    assert 0 <= suffix <= 99
    return self._sendcmd('DA2P', '%02d%02d' % (prefix, suffix))

  def cable_digital_channel(self, prefix, suffix):
    prefix, suffix = map(int, [prefix, suffix])
    assert 1 <= prefix <= 999
    assert 0 <= suffix <= 999
    self._sendcmd('DC2U', '%03d' % prefix)
    self._sendcmd('DC2L', '%03d' % suffix)

  def cable_single_digital_channel(self, num):
    num = int(num)
    assert 1 <= num <= 16382
    if num < 10000:
      cmd = 'DC10'
    else:
      cmd = 'DC11'
    return self._sendcmd(cmd, '%04d' % (num-9999))

  def analog_channel(self, num):
    num = int(num)
    assert 1 <= num <= 135
    return self._sendcmd('DCCH', '%03d' % num)

  def set_channel(self, num, chantype='ota'):
    if chantype == 'ota':
      parts = num.split('.')
      assert len(parts) == 2
      return self.ota_digital_channel(parts[0], parts[1])
    elif chantype == 'cable':
      if '.' in num:
        parts = num.split('.')
        assert len(parts) == 2
        return self.cable_digital_channel(parts[0], parts[1])
      else:
        return self.cable_single_digital_channel(num)
    else:
      return self.analog_channel(num)

  def sleep_timer(self, mode):
    assert mode in [ self.SLEEP_OFF, self.SLEEP_30M, self.SLEEP_60M,
                     self.SLEEP_90M, self.SLEEP_120M ]
    return self._sendcmd('OFTM', mode)

  def position(self):
    #FIXME
    pass

  def av_mode(self):
    #FIXME
    pass
