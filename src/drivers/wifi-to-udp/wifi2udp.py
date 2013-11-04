#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from radiotap import Radiotap
from ieee80211_mgmt import IEEE80211_mgmt
from ieee80211_mgmt import MANAGEMENT
from ieee80211_mgmt import M_BEACON
from ieee80211_beacon import IEEE80211_beacon
from ieee80211_beacon import _MIN_FRAME_SIZE
from binascii import hexlify
from pcap import pcap
from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM
from sys import argv

IEEE_OUI = '\x98\xA7\xB0' # IEEE OUI-24 OF MCST, MOSCOW
TypeWiFi = 1

class wifi2udp():
  "Client interface to receive Wi-Fi beacons."
  def __init__(self, wifi='mon0', host='localhost', port=7777):
    print 'wifi2udp: wifi =' , wifi , ', host =' , host , ', port =' , port
    self.host = gethostbyname(host)
    self.port = port
    self.s = socket(AF_INET, SOCK_DGRAM)
    self.pc = pcap(name=wifi, snaplen=256)

    #f = open('test.pcap')
    #pcap = dpkt.pcap.Reader(f)
    #for ts, buf in pcap:

    self.pc.setfilter('link[0] == 0x80 and ether host de:ad:be:ef:c0:ca')
    print 'listening on %s' % (self.pc.name)

  def process(self, ts, buf):
     "Process one incoming Wi-Fi beacon into one outgoing UDP packet."
     tap = Radiotap(buf)
  
     ieee = IEEE80211_mgmt(buf[tap.length:])
     if ieee.version == 0 and ieee.type == MANAGEMENT and ieee.subtype == M_BEACON:
         '''
  #       print 'IEEE ver %d' % ieee.version ,
  #       print 'type %d' % ieee.type ,
  #       print 'sub %d' % ieee.subtype ,
         print 'BCN' ,
  #       print "%d %x" % (tap.length , tap.present_flags) ,
         print "%d" % (tap.length) ,
  
         if tap.tsft_present:
             print 'tsft %d us' % tap.tsft.usecs ,
  #       if tap.flags_present:
  #           print 'flags %d' % tap.flags.val ,
         if tap.rate_present:
             print 'rate %2d Mbps' % (tap.rate.val / 2) ,
         if tap.channel_present:
             print 'chn %d MHz flags %x' % (tap.channel.freq , tap.channel.flags) ,
         if tap.ant_sig_present:
             print 'sig %d db' % (tap.ant_sig.db) ,
         if tap.ant_present:
             print 'ant %d' % (tap.ant.index) ,
  #       if tap.rx_flags_present:
  #           print 'rx_flags %d' % (tap.rx_flags.val) ,
        '''
  
         if (tap.length + ieee.length) > len(buf):
             print "Incomplete IEEE 802.11 beacon frame" 
  #           continue
         else:
             """
             #print 'fctl %x dur %x' % (ieee.framectl , ieee.duration) ,
             print 'fctl %x' % (ieee.framectl) ,
  
             print hexlify(ieee.data.address1) ,
             print hexlify(ieee.data.address2) ,
             #print hexlify(ieee.data.address3) ,
             print ieee.data.sequence ,
             #print hexlify(buf) , len(buf)
             """
             if len(buf) > tap.length + ieee.length + _MIN_FRAME_SIZE:
                #print len(buf) , tap.length + ieee.length ,  ,
  
                beacon = IEEE80211_beacon(buf[tap.length + ieee.length:])

                #print 'ts' , beacon.timestamp , 'int', beacon.interval , 'cap %x' % beacon.capability ,
                """
                print 'ts' , beacon.timestamp ,
                """
                if beacon.ess_present == 1:
                  #print 'len' , beacon.essid.length ,
                  #print 'SSID' , beacon.essid.ssid ,
                  #print beacon.essid.ssid

                  #self.s.sendto(beacon.essid.ssid, (self.host, self.port))
                  #ts = beacon.timestamp
                  
                  (id , lat, lgt, alt) = beacon.essid.ssid.split("_")
                  ts    = '0'
                  track = '0'
                  speed = '0'
                  if beacon.vendor_present == 1 and beacon.vendor.space[:len(IEEE_OUI)] == IEEE_OUI:
                    (ts, track, speed) = beacon.vendor.space[len(IEEE_OUI):].split("_")
                    #print ts, track, speed
                  pkt = "%s %s %s %s %s %s %s %u" % ( ts, id, \
                    lat, lgt, alt, track, speed, TypeWiFi )
                  self.s.sendto(pkt, (self.host, self.port))

                  #print
                else:
                  print "SSID is missing"
             else:
                print "Incomplete IEEE 802.11 beacon frame"

if __name__ == '__main__':

  #import resource
  #resource.setrlimit(resource.RLIMIT_AS, (11 * 1048576L, -1L))

  opts = { }
  argc = len(argv)
  if argc > 1:
    opts["wifi"]    = argv[1]
  
  if argc > 2:
    opts["host"]    = argv[2]
  
  if argc > 3:
    opts["port"]    = int(argv[3])

  session = wifi2udp(**opts)
  session.pc.loop(session.process)

#f.close()

