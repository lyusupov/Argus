#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import gps
#from time import sleep

session = gps.gps()
session.read()
session.stream()

cycles = 0

while 1:
    session.read()

    #print 'Fix mode           ' , session.fix.mode
    #print 'Fix                ' , ("NO_FIX","FIX","DGPS_FIX")[session.fix.mode - 1]
    #print 'Satellites in use: ', session.satellites_used
    if (session.fix.mode > 1):
      cycles = cycles + 1
      if cycles > 3: # 1 GSV per 4 RMC on Sirf
        print session.satellites_used
        break
    else:
      cycles = 0

    #sleep(1)
