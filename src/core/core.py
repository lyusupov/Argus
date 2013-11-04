#!/usr/bin/python
# -*- coding: utf-8 -*-

import thread
import time
from socket import socket, gethostbyname, AF_INET, \
    SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
from sys import argv, exit
from motionless import DecoratedMap, LatLonMarker, Marker
from misc import EarthDistance, MeterOffset, Rad2Deg
from math import atan2

TRANSMIT_INTERVAL       = 0.5                   # seconds
#TZSHIFT                 = 0                     # milliseconds
TZSHIFT                 = time.timezone * 1000  # milliseconds
ELEMENT_EXPIRATION_TIME = (15 * 1000)           # milliseconds
EXPIRATION_CYCLE        = 5                     # seconds
MAP_CYCLE               = 30                    # seconds
PROXIMITY_CYCLE         = 1 # 0.5                   # seconds

TypeGPS       = 0
TypeADSB      = 1

class DispatchElement:
  "Element of dispatch table."
  def __init__(self, tstamp, id, lat, lgt, alt, track, speed, type):

    # print 'DispatchElement: tstamp =' , tstamp , ', id =' , id , \
    #  ', lat =' , lat , ', lgt =' , lgt , ', alt =' , alt ,\
    #  ', track =' , track , ', speed =' , speed , ', type =' , type 
    # self.lock = thread.allocate_lock()
    self.tstamp = tstamp
    self.id = id
    self.lat = lat
    self.lgt = lgt
    self.alt = alt
    self.track = track
    self.speed = speed
    self.type = type

class Traffic:
  "Element of per-aircraft traffic table."
  def __init__(self, dist, azim, alt_diff, id, track, speed):
    self.dist = dist
    self.azim = azim
    self.alt_diff = alt_diff
    self.id = id
    self.track = track
    self.speed = speed

class Display:
  "Fill a page with traffic and submit to UDP-connected display."
  def __init__(self, sock, host, port):
    self.frame = []
    self.sock = sock
    self.host = host
    self.port = port

  def clear(self):
    self.frame = []

  def mark(self, dist, azim, diff, id):
    self.frame += "%f %f %f %s\n" % ( dist , azim , diff, id)

  def draw(self):
    self.buf = "".join( self.frame )
    #print self.buf
    self.sock.sendto(self.buf, (self.host, self.port))

def sortByDist(traffic):
        return traffic.dist

def Transmit(dlist, dlock, dst, host, port):
  "Transmit element(s) of dispatch table."
  while True:
    dlock.acquire()
    for element in dlist:
      #ndx = dlist.index(element)
      #print 'Entry [' , ndx, '], tstamp = ' , element.tstamp, \
      #  ', id =' , element.id, ', lat =' , element.lat
      buf = "%s_%s_%s_%s %u_%s_%s" %  \
          ( element.id, element.lat, element.lgt, element.alt, \
          element.tstamp, element.track, element.speed )
      dst.sendto(buf, (host, port))
    dlock.release()
    time.sleep(TRANSMIT_INTERVAL)

def Expire(dlist, dlock, MyId):
  "Delete expired element(s) of dispatch table."
  while True:
    __to_remove = []

    #Iaminlist = False
    #dlock.acquire()
    #for element in dlist:
    #  if element.id == MyId:
    #    MyTime = element.tstamp
    #    Iaminlist = True
    #dlock.release()

    #if Iaminlist: 
    #  print MyTime

    dlock.acquire()
    for element in dlist:
        #print '***' , long(time.time()*1000) + TZSHIFT , element.tstamp , long(time.time()*1000) + TZSHIFT - element.tstamp
        if long(time.time()*1000) + TZSHIFT - element.tstamp > ELEMENT_EXPIRATION_TIME:
          print 'Delete element with id: ' , element.id
          __to_remove.append(element)
    for element in __to_remove:
      dlist.remove(element)
    dlock.release()
    time.sleep(EXPIRATION_CYCLE)

def Map(dlist, dlock):
  "Create a Google map of traffic."
  while True:
    dmap = DecoratedMap(maptype = 'hybrid', size_x = 640, size_y = 640)
    dlock.acquire()
    ndx = len(dlist)
    for element in dlist:
      i = dlist.index(element)
      label = Marker.LABELS[i]
      dmap.add_marker(LatLonMarker(element.lat,element.lgt,color='red',size='mid',label=label))
    dlock.release()
    if ndx > 0:
      print dmap.generate_url()
    time.sleep(MAP_CYCLE)

def Proximity(dlist, dlock, display_sock, display_host, display_port, MyId, NorthUp):
  "Create traffic proximity table for my aircraft."

  display = Display(display_sock, display_host, display_port)

  while True:
    OtherTrafiic = []
    Iaminlist = False
    dlock.acquire()
    for element in dlist:
      #print element.id
      if element.id == MyId:
        Me = element
        Iaminlist = True
      else:
        OtherTrafiic.append(element) 
    dlock.release()

    if Iaminlist: 
      ProximityList = []

      for element in OtherTrafiic:
        mylat = float(Me.lat)
        mylgt = float(Me.lgt)
        myalt = float(Me.alt)
        mytrk = float(Me.track)
        trlat = float(element.lat)
        trlgt = float(element.lgt)
        tralt = float(element.alt)
        dist = EarthDistance((trlat, trlgt), (mylat, mylgt))
        (dx, dy) = MeterOffset((trlat, trlgt), (mylat, mylgt))
    
        math_angle = Rad2Deg(atan2(dy , dx))

        azim = 90 - math_angle
        if NorthUp is False:
          azim = azim - mytrk
        azim = (azim + 360) % 360
    
        alt_diff = tralt - myalt
        id = element.id
        track = float(element.track)
        speed = float(element.speed)
        traffic = Traffic(dist, azim, alt_diff, id, track, speed)
        ProximityList.append(traffic)
    
      #for element in ProximityList:
      #  print element.dist, element.azim, element.alt_diff, element.id
    
      ProximityList.sort(key=sortByDist)
    
      if len(ProximityList) > 0:
        display.clear()
      for element in ProximityList:
        print element.dist, element.azim, element.alt_diff, element.id
        display.mark(element.dist, element.azim, element.alt_diff, element.id)
      if len(ProximityList) > 0:
        print
        display.draw()

    time.sleep(PROXIMITY_CYCLE)

class udp2dispatch():
  "Core info dispatcher."
  def __init__(self, src_host='localhost', src_port=7777, \
    export_host='localhost', export_port=7778, \
    display_host='localhost', display_port=7779, MyId='99', NorthUp=1):

    print 'udp2dispatch: src_host =' , src_host , ', src_port =' , src_port, \
      ' export_host =' , export_host , ', export_port =' , export_port , \
      ' display_host =' , display_host , ', display_port =' , display_port , \
      ', MyId =', MyId , ', NorthUp =', NorthUp
    self.s = socket(AF_INET, SOCK_DGRAM)
    self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self.src_host = gethostbyname(src_host)
    self.s.bind((self.src_host, src_port))
    self.export_host = gethostbyname(export_host)
    self.export_port = export_port
    self.e = socket(AF_INET, SOCK_DGRAM)
    self.display_host = gethostbyname(display_host)
    self.display_port = display_port
    self.d = socket(AF_INET, SOCK_DGRAM)
    self.MyId = MyId
    self.NorthUp = bool(NorthUp)

    self.DispatchList = [ ]
    self.DispatchLock = thread.allocate_lock()
  
    thread.start_new(Transmit, (self.DispatchList, self.DispatchLock, self.e , \
      self.export_host, self.export_port))
    thread.start_new(Expire, (self.DispatchList, self.DispatchLock, self.MyId))
    #thread.start_new(Map, (self.DispatchList, self.DispatchLock))
    thread.start_new(Proximity, (self.DispatchList, self.DispatchLock, \
      self.d , self.display_host, self.display_port , self.MyId, self.NorthUp))

  def Add(self, tstamp, id, lat, lgt, alt, track, speed, type):
    "Create or update element of dispatch table."
    # print 'DispatchElement: tstamp =' , tstamp , ', id =' , id , \
    #  ', lat =' , lat , ', lgt =' , lgt , ', alt =' , alt ,\
    #  ', track =' , track , ', speed =' , speed , ', type =' , type 
    # self.lock = thread.allocate_lock()
    self.DispatchLock.acquire()
  
    for element in self.DispatchList:
      # print 'element.id: ', element.id , ' id: ' , id
      if id == element.id:
        #print 'type: ', type ,
        if tstamp > element.tstamp:
          #print "incoming packet has most recent timestamp "
          element.tstamp = tstamp
          # element.id = id
          element.lat = lat
          element.lgt = lgt
          element.alt = alt
          element.track = track
          element.speed = speed
          element.type = type
        #else:
          #if tstamp == element.tstamp:
            #print "incoming packet has same timestamp "
          #else:
            #print "incoming packet has timestamp is in past "
        break
      else:
        if element == self.DispatchList[-1]:
          self.DispatchList.append(DispatchElement(tstamp, id, lat, lgt, alt, track, speed, type))
          break
        else:
          continue
    else:
      # print 'Append id: ', id
      self.DispatchList.append(DispatchElement(tstamp, id, lat, lgt, alt, track, speed, type))
  
    self.DispatchLock.release()

  def process(self):
      "Process one incoming UDP packet into one dispatch record."

      message, address = self.s.recvfrom(8192)

      arr = message.split(" ")
      tstamp = long(arr[0])
      id = arr[1]
      lat = arr[2]
      lgt = arr[3]
      alt = arr[4]
      track = arr[5]
      speed = arr[6]
      type = int(arr[7])

      # Over-ride time stamp for ADS-B message with data from GMT local clock
      if type == TypeADSB:
        tstamp = long(time.time()*1000) + TZSHIFT

      self.Add(tstamp, id, lat, lgt, alt, track, speed, type)

if __name__ == '__main__':

  opts = { }
  argc = len(argv)
  if argc > 1:
    opts["src_host"]    = argv[1]
  
  if argc > 2:
    opts["src_port"]    = int(argv[2])  
  
  if argc > 3:
    opts["export_host"]    = argv[3]
  
  if argc > 4:
    opts["export_port"]    = int(argv[4])

  if argc > 5:
    opts["display_host"]    = argv[5]
  
  if argc > 6:
    opts["display_port"]    = int(argv[6])

  if argc > 7:
    opts["MyId"]        = argv[7]

  if argc > 8:
    opts["NorthUp"]        = int(argv[8])

  session = udp2dispatch(**opts)
  while True:
    session.process()
