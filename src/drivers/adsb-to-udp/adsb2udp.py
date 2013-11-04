#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from socket import socket, gethostbyname, getaddrinfo, error, \
  AF_INET, SOCK_STREAM, SOCK_DGRAM
from sys import argv, stderr
from time import time

NaN = float('nan')

TypeADSB       = 1

class aircraft:
    def __init__(self):
        self.id = ""                # ICAO Id
        self.latitude = self.longitude = 0.0
        self.altitude = NaN         # Feet

class adsb2udp():
  "SBS client interface to ADS-B."
  def __init__(self, src_host='localhost', src_port=30003, device='', \
    my_Id='TEST', dst_host='localhost', dst_port=7777):
    print 'adsb2udp: src host =' , src_host , ', src_port =' , src_port , \
    ', dst_host =' , dst_host , ', dst_port =' , dst_port
    self.verbose = 0
    self.linebuffer = ""
    self.sock = None        # in case we blow up in connect
    self.pos = aircraft()
    self.device = device
    self.src_host = gethostbyname(src_host)
    self.src_port = src_port
    self.dst_host = gethostbyname(dst_host)
    self.dst_port = dst_port
    if src_host != None:
        self.connect(src_host, src_port)
    self.d = socket(AF_INET, SOCK_DGRAM)


  def connect(self, host, port):
    """Connect to a host on a given port."""

    msg = "getaddrinfo returns an empty list"
    self.sock = None
    for res in getaddrinfo(host, port, 0, SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            self.sock = socket(af, socktype, proto)
            #if self.debuglevel > 0: print 'connect:', (host, port)
            self.sock.connect(sa)
        except error, msg:
            #if self.debuglevel > 0: print 'connect fail:', (host, port)
            self.close()
            continue
        break
    if not self.sock:
        raise error, msg

  def close(self):
      if self.sock:
          self.sock.close()
      self.sock = None

  def __del__(self):
      self.close()

  def read(self):
      "Wait for and read data being streamed from the daemon."
      if self.verbose > 1:
          stderr.write("poll: reading from daemon...\n")
      eol = self.linebuffer.find('\n')
      if eol == -1:
          frag = self.sock.recv(4096)
          self.linebuffer += frag
          if self.verbose > 1:
              stderr.write("poll: read complete.\n")
          if not self.linebuffer:
              if self.verbose > 1:
                  stderr.write("poll: returning -1.\n")
              # Read failed
              return -1
          eol = self.linebuffer.find('\n')
          if eol == -1:
              if self.verbose > 1:
                  stderr.write("poll: returning 0.\n")
              # Read succeeded, but only got a fragment
              return 0
      else:
          if self.verbose > 1:
              stderr.write("poll: fetching from buffer.\n")

      # We got a line
      eol += 1
      self.response = self.linebuffer[:eol]
      self.linebuffer = self.linebuffer[eol:]

      # Can happen if daemon terminates while we're reading.
      if not self.response:
          return -1
      if self.verbose:
          stderr.write("poll: data is %s\n" % repr(self.response))
      self.received = time()
      # We got a \n-terminated line
      return len(self.response)

  def unpack(self, buf):

      fields = buf.strip().split(",")
      if fields[0] == "MSG" and fields[1] == "3":
        self.pos.id = fields[4]
        self.latitude = self.longitude = 0.0
        self.altitude = NaN         # Feet
        if fields[11] != '':
          self.pos.altitude = float(fields[11])
        if fields[14] != '':
          self.pos.latitude = float(fields[14])
        if fields[15] != '':
          self.pos.longitude = float(fields[15])


  def process(self):
    "Process one incoming ADS-B message into one outgoing UDP packet."

    try:
      while True:
  
        self.read()

        if self.response.startswith("MSG,3") :
            self.unpack(self.response)
            #print '----------------------------------------'
            #print ' ADS-B reading'
            #print '----------------------------------------'
            #print 'id          ' , self.pos.id
            #print 'latitude    ' , self.pos.latitude
            #print 'longitude   ' , self.pos.longitude
            #print 'altitude    ' , self.pos.altitude

            buf = "%s %s %f %f %.1f %.1f %.1f %u" % ( 0, self.pos.id, \
              self.pos.latitude, self.pos.longitude, self.pos.altitude / 3.2808, \
              0, 0 , TypeADSB )

            #print buf
    
            self.d.sendto(buf, (self.dst_host, self.dst_port))
  
    except KeyboardInterrupt:
      # Avoid garble on ^C
      print ""

if __name__ == '__main__':

  opts = { }

  argc = len(argv)
  if argc > 1:
    opts["src_host"]    = argv[1]
  
  if argc > 2:
    opts["src_port"]    = int(argv[2])

  if argc > 3:
    opts["dst_host"]    = argv[3]
  
  if argc > 4:
    opts["dst_port"]    = int(argv[4])
  
  session = adsb2udp(**opts)
  session.process()

# driver.py ends here
