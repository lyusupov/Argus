#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import gps
from datetime import datetime , timedelta
import iso8601

def _linux_set_time(dt):
    import ctypes
    import ctypes.util
    import time

    # /usr/include/linux/time.h:
    #
    # define CLOCK_REALTIME                     0
    CLOCK_REALTIME = 0

    # /usr/include/time.h
    #
    # struct timespec
    #  {
    #    __time_t tv_sec;            /* Seconds.  */
    #    long int tv_nsec;           /* Nanoseconds.  */
    #  };
    class timespec(ctypes.Structure):
        _fields_ = [("tv_sec", ctypes.c_long),
                    ("tv_nsec", ctypes.c_long)]

    librt = ctypes.CDLL(ctypes.util.find_library("rt"))

    ts = timespec()
    ts.tv_sec = int( time.mktime( dt.timetuple() ) )
    ts.tv_nsec = dt.microsecond * 1000 # microsecond to nanosecond

    # http://linux.die.net/man/3/clock_settime
    librt.clock_settime(CLOCK_REALTIME, ctypes.byref(ts))

if __name__ == '__main__':

  session = gps.gps()
  session.read()
  session.stream()
  
  while 1:
      session.read()
      st = datetime.utcnow()
      #print 'Fix                ' , ("NO_FIX","FIX","DGPS_FIX")[session.fix.mode - 1]
      #print 'GPS time utc    ' , session.utc
      #print 'System time utc ' , st
  
      if session.utc != '' and session.utc != None:
        gt = iso8601.parse_date(session.utc)
        td = st - gt.replace(tzinfo=None)
        #print 'time differential ' , td.total_seconds()

        # Workaround against NTPD SHM 4 hours issue https://bugs.ntp.org/417 
        if (abs(td.total_seconds()) > 4 * 60 * 60):
            _linux_set_time(gt)
            break
  
        if (session.fix.mode > 1):
          if (abs(td.total_seconds()) < 1):
            print td.total_seconds()
            break
  
      #sleep(1)
