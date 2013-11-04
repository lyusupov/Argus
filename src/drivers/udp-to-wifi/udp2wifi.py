#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from radiotap import Radiotap
from ieee80211_mgmt import IEEE80211_mgmt
from ieee80211_mgmt import MANAGEMENT
from ieee80211_mgmt import M_BEACON
from ieee80211_beacon import IEEE80211_beacon
from ieee80211_beacon import _EID_ESSID, _EID_RATES_SUP, _EID_DSSS, \
    _EID_VENDOR, CAP_ESS, _MAX_SSID_SIZE

from binascii import hexlify
from sys import argv
from pcap import pcap
from time import sleep
from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM, \
      SOL_SOCKET, SO_REUSEADDR
from struct import pack

IEEE_OUI = '\x98\xA7\xB0' # IEEE OUI-24 OF MCST, MOSCOW

class udp2wifi():
  "Client interface to transmit Wi-Fi beacons."
  def __init__(self, host='localhost', port=7777, wifi='mon0', channel=1):
    self.channel = channel
    print 'udp2wifi: host =' , host , ', port =' , port , ', wifi =' , wifi , \
      ', channel =' , self.channel , '(' , 2407 + self.channel * 5 , ')'

    self.s = socket(AF_INET, SOCK_DGRAM)
    self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self.host = gethostbyname(host)
    self.s.bind((self.host, port))
    self.pc = pcap(name=wifi, snaplen=256)

  def process(self):
    "Process one incoming UDP packet into one outgoing Wi-Fi beacon."
    message, address = self.s.recvfrom(8192)
    arr = message.split(" ")
    m_len = len(arr)

    if m_len > 0:
      m_body = arr[0]

    if m_len > 1:
      m_rest = arr[1]
    else:
      m_rest = ''

    #print m_body , m_rest

    b_ssid       = m_body[:_MAX_SSID_SIZE]
    b_timestamp  = 0x0123456789ABCDEF
    b_interval   = 100
    b_capability = (1 << CAP_ESS)
    #b_ssid       = 'TEST'
    b_ssid_len   = len(b_ssid)
    b_rates      = '\x82' # 1Mb/s
    b_rates_len  = len(b_rates)
    b_channel    = pack('B', self.channel)
    b_dss_len    = len(b_channel)
    b_oui        = IEEE_OUI
    b_space      = ' PROXIMITY WARNING DEVICE '
    if m_rest != '':
      b_space    = m_rest
    b_vendor     = b_oui + b_space
    b_vendor_len = len(b_vendor)
    
    ess    = IEEE80211_beacon.ESS   ( eid = _EID_ESSID , length = b_ssid_len , data = b_ssid )
    rates  = IEEE80211_beacon.Rates ( eid = _EID_RATES_SUP , length = b_rates_len , data = b_rates )
    dsss   = IEEE80211_beacon.DSSS  ( eid = _EID_DSSS , length = b_dss_len , data = b_channel )
    vendor = IEEE80211_beacon.Vendor( eid = _EID_VENDOR , length = b_vendor_len , data = b_vendor )
    
    eids_pack = IEEE80211_beacon.ESS.pack(ess)     + \
                IEEE80211_beacon.Rates.pack(rates) + \
                IEEE80211_beacon.DSSS.pack(dsss)   + \
                IEEE80211_beacon.Vendor.pack(vendor)
    
    beacon = IEEE80211_beacon ( timestamp = b_timestamp , interval = b_interval,
                capability = b_capability , data = eids_pack )
    
    m_address  = '\xDE\xAD\xBE\xEF\xC0\xCA'
    m_sequence = 100
    
    frame = IEEE80211_mgmt (
               version = 0 , type = MANAGEMENT, subtype = M_BEACON , order = 0 ,
               data = IEEE80211_mgmt.Management (
                    address1 = '\xFF\xFF\xFF\xFF\xFF\xFF' , address2 = m_address ,
                    address3 = m_address , sequence = m_sequence ,
                    data = beacon ))
    
    r_flags    = 0 
    r_rate     = 2
    r_freq     = 2407 + self.channel * 5
    r_ch_flags = 0x00a0
    r_signal   = -85
    r_antenna  = 1
    r_rx_flags = 0
    
    tap = Radiotap (
            data = Radiotap.Flags ( val = r_flags ,
              data = Radiotap.Rate ( val = r_rate ,
                data = Radiotap.Channel ( freq = r_freq , flags = r_ch_flags ,
                  data = Radiotap.AntennaSignal ( db = r_signal ,
                    data = Radiotap.Antenna ( index = r_antenna ,
                      data = Radiotap.RxFlags ( val = r_rx_flags ,
                        data = frame )))))))
    
    tap.length=len(tap) - len(frame)
    tap.flags_present=1
    tap.rate_present=1
    tap.channel_present=1
    tap.ant_sig_present=1
    tap.ant_present=1
    tap.rx_flags_present=1
    
    pkt = str(tap)
    #print hexlify(pkt)
    #print pkt ,
    
    #f = open('test.pcap','wb')
    #pcap = dpkt.pcap.Writer(f, linktype=dpkt.pcap.DLT_IEEE802_11_RADIO)
    #pcap.writepkt(tap)
    #pcap.close()
    
    self.pc.sendpacket(Radiotap.pack(tap))
  
if __name__ == '__main__':

  opts = { }
  argc = len(argv)
  if argc > 1:
    opts["host"]    = argv[1]
  
  if argc > 2:
    opts["port"]    = int(argv[2])
  
  if argc > 3:
    opts["wifi"]    = argv[3]

  if argc > 4:
    opts["channel"] = int(argv[4])

  session = udp2wifi(**opts)
 
  while True:
    session.process()


