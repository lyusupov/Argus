#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM, \
      SOL_SOCKET, SO_REUSEADDR
from sys import argv
import serial
import re
from math import sin, cos, radians

class udp2pda:
  "Transfer data to PDA (Flarm format)."
  def __init__(self, host='localhost', port=7779, \
    device='/dev/ttyUSB1', scale=400 ):
    print 'udp2pda: host =' , host , ', port =' , port , \
      ', device =' , device , ', scale =' , scale
    self.scale = scale
    self.s = socket(AF_INET, SOCK_DGRAM)
    self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self.host = gethostbyname(host)
    self.s.bind((self.host, port))
    self.tty = serial.Serial(device, 19200, timeout=1)


  """ Calculate  the checksum for NMEA sentence 
      from a GPS device. An NMEA sentence comprises
      a number of comma separated fields followed by
      a checksum (in hex) after a "*". An example
      of NMEA sentence with a correct checksum (of
      0x76) is:
      
        GPGSV,3,3,10,26,37,134,00,29,25,136,00*76"
  """
  
  def checksum(self, sentence):
  
      """ Remove leading $ """
      sentence = sentence.lstrip('$')
  
      nmeadata,cksum = re.split('\*', sentence)
      #print nmeadata
      calc_cksum = 0
      for s in nmeadata:
          calc_cksum ^= ord(s)
  
      return calc_cksum

  def process(self):
      "Process one incoming UDP packet."

      message, address = self.s.recvfrom(8192)

      page = message.split("\n")
      for record in page:
        if len(record) > 0:
          arr = record.split(" ")
          distance = float(arr[0])
          azimuth = float(arr[1])
          diff = float(arr[2])
          id = arr[3]
          bearing = int(azimuth)
          if bearing > 180:
            bearing = bearing - 360
          #print distance , azimuth
          str1 = "$PFLAU,%d,1,1,1,%d,2,%d,%u,%s*" % \
            ( len(page)-1, bearing, int(diff), int(distance), id )
          csum = self.checksum(str1)
          str1 += "%02x\r\n" % csum
          #print str1
          self.tty.write(str1)
          # XCSoar ignores warning data from PFLAU
          azim_rad = radians(azimuth)
          str2 = "$PFLAA,2,%d,%d,%d,2,%s,,,,,1*" % \
            ( int(distance * cos(azim_rad)), int(distance * sin(azim_rad)),\
              int(diff), id )
          csum = self.checksum(str2)
          str2 += "%02x\r\n" % csum
          #print str2
          self.tty.write(str2)

if __name__ == '__main__':

  opts = { }
  argc = len(argv)
  if argc > 1:
    opts["host"]    = argv[1]
  
  if argc > 2:
    opts["port"]    = int(argv[2])
  
  if argc > 3:
    opts["device"]    = argv[3]

  if argc > 4:
    opts["scale"]    = int(argv[4])

  session = udp2pda(**opts)

  while True:
    session.process()
