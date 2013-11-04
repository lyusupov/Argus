#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from gps2udp  import gps2udp
from wifi2udp import wifi2udp
from udp2wifi import udp2wifi
#from udp2db   import udp2db
from udp2led  import udp2led
from core     import udp2dispatch
from adsb2udp import adsb2udp
from udp2pda  import udp2pda
from time     import sleep
from sys import argv
import thread 

def gps2udp_thread(id):
  opts = { "src_host" : 'localhost' , "src_port" : 2947 , \
    "device" : '' , \
    "my_Id" : id, "dst_host" : 'localhost', "dst_port" : 7777 }
  session = gps2udp(**opts)
  session.process()
  thread.exit()

def wifi2udp_thread():
  opts = { "wifi" : 'wlan1' , "host" : 'localhost', "port" : 7777 }
  session = wifi2udp(**opts)
  session.pc.loop(session.process)
  thread.exit()

def udp2wifi_thread():
  opts = { "port" : 7778, "wifi" : 'wlan1' , "channel" : 1 }
  session = udp2wifi(**opts)
  while True:
    session.process()
  thread.exit()

def udp2db_thread():
  opts = { "host" : 'localhost' , "port" : 7778, "database" : '/tmp/traffic.db' }
  session = udp2db(**opts)
  while True:
    session.process()
  thread.exit()

def udp2led_thread():
  opts = { "host" : 'localhost' , "port" : 7779, \
    "device" : '/dev/ttyUSB1' , "scale" : 400}
  session = udp2led(**opts)
  while True:
    session.process()
  thread.exit()

def adsb2udp_thread():
  opts = { "src_host" : '192.168.157.198' , "src_port" : 30003, \
    "dst_host" : 'localhost' , "dst_port" : 7777 }
  session = adsb2udp(**opts)
  while True:
    session.process()
  thread.exit()

def udp2pda_thread():
  opts = { "host" : 'localhost' , "port" : 7779, \
    "device" : '/dev/ttyUSB1' }
  session = udp2pda(**opts)
  while True:
    session.process()
  thread.exit()

def core_thread(id):
  opts = { "src_host" : 'localhost' , "src_port" : 7777, \
    "export_host" : 'localhost' , "export_port" : 7778, \
    "display_host" : 'localhost' , "display_port" : 7779, \
    "MyId" : id , "NorthUp" : 1}
  session = udp2dispatch(**opts)
  while True:
    session.process()
  thread.exit()

if __name__ == '__main__':

  opts = { }

  argc = len(argv)
  if argc > 1:
    Id    = argv[1]

  thread.start_new(gps2udp_thread, (Id,))
  thread.start_new(wifi2udp_thread, ())
  thread.start_new(udp2wifi_thread, ())
  #thread.start_new(udp2db_thread, ())
  thread.start_new(udp2led_thread, ())
  #thread.start_new(adsb2udp_thread, ())
  #thread.start_new(udp2pda_thread, ())
  thread.start_new(core_thread, (Id,))

  while True:
    "Do nothing"
    sleep(10)
