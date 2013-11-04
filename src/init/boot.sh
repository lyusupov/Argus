#!/bin/sh

DEVICE="/dev/ttyUSB1"
SPEED=19200

PGPSPATH=/ProxWarnDev/lib/gpsd-3.5
PLIBPATH=/ProxWarnDev/drivers/gpsd-to-udp

stty -F $DEVICE $SPEED -hupcl

sleep 2

./ColorduinoPutChar.py 11 2 $DEVICE $SPEED

sleep 1

./ColorduinoPutChar.py 16 1 $DEVICE $SPEED

SATTELITES=`PYTHONPATH=$PGPSPATH:$PLIBPATH ./GPSWaitFix.py`

./ColorduinoPutChar.py 16 2 $DEVICE $SPEED

sleep 1

./ColorduinoPutChar.py $SATTELITES 4 $DEVICE $SPEED

sleep 3

./ColorduinoPutChar.py 29 1 $DEVICE $SPEED

TIMEDIFF=`PYTHONPATH=$PGPSPATH:$PLIBPATH ./GPSSyncTime.py`

./ColorduinoPutChar.py 29 2 $DEVICE $SPEED

/ProxWarnDev/core/start.sh

