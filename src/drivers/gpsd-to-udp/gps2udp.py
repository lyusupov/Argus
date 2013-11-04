#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from gps import gps
from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM
from sys import argv
import iso8601, time
#from misc import isotime

WATCH_ENABLE	= 0x000001	# enable streaming
WATCH_DISABLE	= 0x000002	# disable watching
WATCH_DEVICE	= 0x000800	# watch specific device

TypeGPS       = 0

class gps2udp():
  "Client interface to GPSD."
  def __init__(self, src_host='localhost', src_port=2947, device='', \
    my_Id='TEST', dst_host='localhost', dst_port=7777):
    print 'gps2udp: src host =' , src_host , ', src_port =' , src_port , \
    ', device =' , device , ', my_Id =' , my_Id , \
    ', dst_host =' , dst_host , ', dst_port =' , dst_port
    opts = { }
    opts["host"]    = src_host
    opts["port"]    = src_port
    self.gps_session = gps(**opts)
    self.device = device
    self.my_Id = my_Id
    self.host = gethostbyname(dst_host)
    self.port = dst_port
    self.s = socket(AF_INET, SOCK_DGRAM)

  def process(self):
    "Process one incoming GPS message into one outgoing UDP packet."
    session = self.gps_session
    #session.read()
    session.stream(WATCH_DEVICE, self.device)
    #session.stream(WATCH_ENABLE)

    try:
      while True:
  
        session.read()
  
        #print
        #print ' GPS reading'
        #print '----------------------------------------'
        #print 'fix         ' , ("NO_FIX","FIX","DGPS_FIX")[session.fix.mode - 1]
        #print 'latitude    ' , session.fix.latitude
        #print 'longitude   ' , session.fix.longitude
        #print 'time utc    ' , session.utc # , session.fix.time
        #print 'altitude    ' , session.fix.altitude
        #print 'track       ' , session.fix.track
        #print 'speed       ' , session.fix.speed
        #print
        #buf = "%s_%f_%f_%06.1f" % ( my_Id, session.fix.latitude, \
        #session.fix.longitude, session.fix.altitude )

        tstamp = 0
        if session.utc != '':
          dt = iso8601.parse_date(session.utc)
          tstamp = long(time.mktime(dt.timetuple())*1000 + dt.microsecond/1000)

        #print tstamp ,
        #tstamp1 = 0
        #if session.utc != '':
        #  tstamp1 = long(isotime(session.utc)*1000)
        #print tstamp1 , tstamp1 - tstamp 

        buf = "%s %s %f %f %.1f %.1f %.1f %u" % ( tstamp, self.my_Id, \
          session.fix.latitude, session.fix.longitude, session.fix.altitude, \
          session.fix.track, session.fix.speed , TypeGPS )
        self.s.sendto(buf, (self.host, self.port))
  
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
    opts["device"]      = argv[3]

  if argc > 4:
    opts["my_Id"]       = argv[4]

  if argc > 5:
    opts["dst_host"]    = argv[5]
  
  if argc > 6:
    opts["dst_port"]    = int(argv[6])
  
  session = gps2udp(**opts)
  session.process()

# driver.py ends here
