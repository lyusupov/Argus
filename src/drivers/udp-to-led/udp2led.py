#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import thread
import time
from math import sin, cos, radians
from Colorduino import Colorduino
from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM, \
      SOL_SOCKET, SO_REUSEADDR
from sys import argv

#DISTANCE = 695.617418904
#AZIMUTH  = 274.870418914
#DISTANCE = 800
#AZIMUTH  = 330

#SCALE_FACTOR = 400 # meters
SQUARE_ROOT_OF_TWO = 1.4143

COLOR_RED    = 0xFF0000
COLOR_YELLOW = 0xFF8000
COLOR_GREEN  = 0x00FF00
COLOR_WRITE  = 0xFFFFFF
COLOR_WRITE_LOW_INTENSITY = 0x808080
ARROW_COLOR = COLOR_WRITE_LOW_INTENSITY

CENTER_OFFSET_X = 4
CENTER_OFFSET_Y = 4

DISPLAY_EXPIRATION_CYCLE = 10 # seconds

class udp2led:
  "Display device driver."
  def __init__(self, host='localhost', port=7779, \
    device='/dev/ttyUSB1', scale=400 ):
    print 'udp2led: host =' , host , ', port =' , port , \
      ', device =' , device , ', scale =' , scale
    self.scale = scale
    self.s = socket(AF_INET, SOCK_DGRAM)
    self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self.host = gethostbyname(host)
    self.s.bind((self.host, port))
    self.screen = Colorduino (device)
    self.status = [ False ] # mutable type to pass a variable for a thread by reference
    self.DisplayLock = thread.allocate_lock()
    thread.start_new(ClearExpired, (self.screen, self.DisplayLock, self.status))

  def PlaceTrafficMark(self, distance, azimuth):
    "Display a traffic."

    vec_l = distance / self.scale

    # Get rid of "arrow" area 
    if vec_l < SQUARE_ROOT_OF_TWO:
       vec_l = SQUARE_ROOT_OF_TWO

    vec_angle = radians(45 - azimuth)
    vec_x = cos(vec_angle) * vec_l
    vec_y = sin(vec_angle) * vec_l
    
    disp_vector_x = vec_x + CENTER_OFFSET_X
    disp_vector_y = vec_y + CENTER_OFFSET_Y
    
    #print disp_vector_x , disp_vector_y
    
    dot_x = int(disp_vector_x)
    dot_y = int(disp_vector_y)
    proximity = int(vec_l)

    #print dot_x , dot_y , proximity

    # Draw an "arrow" pointing into direction of motion
    self.screen.Point(CENTER_OFFSET_X, CENTER_OFFSET_Y, ARROW_COLOR)
    self.screen.Point(CENTER_OFFSET_X - 1, CENTER_OFFSET_Y, ARROW_COLOR)
    self.screen.Point(CENTER_OFFSET_X, CENTER_OFFSET_Y - 1, ARROW_COLOR)

    if dot_x >= 0 and dot_x < 8 and dot_y >= 0 and dot_y < 8:
      if proximity == 0:
        color = COLOR_RED
      elif proximity == 1:
        color = COLOR_RED
      elif proximity == 2:
        color = COLOR_YELLOW
      else:
        color = COLOR_GREEN
      self.screen.Point(dot_x, dot_y, color)

  def Draw(self):
    "Send screen to low-level display device."
    self.DisplayLock.acquire()
    self.screen.Draw()
    self.DisplayLock.release()

  def Clear(self):
    "Clear all traffic."
    self.DisplayLock.acquire()
    self.screen.Clear()
    self.DisplayLock.release()

  def process(self):
      "Process one incoming UDP packet."

      message, address = self.s.recvfrom(8192)

      self.DisplayLock.acquire()
      self.screen.Clear()

      page = message.split("\n")
      for record in page:
        if len(record) > 0:
          arr = record.split(" ")
          distance = float(arr[0])
          azimuth = float(arr[1])
          #print distance , azimuth
          self.PlaceTrafficMark(distance, azimuth)

      self.screen.Draw()
      self.status[0] = True
      self.DisplayLock.release()

def ClearExpired(Screen, DisplayLock, StatusList):
  "Clear screen if no packets received after specific time elapsed."
  while True:
    DisplayLock.acquire()
    if StatusList[0] is True:
      StatusList[0] = False
    else:
      Screen.Clear()
      # Draw an "arrow" pointing into direction of motion
      Screen.Point(CENTER_OFFSET_X, CENTER_OFFSET_Y, ARROW_COLOR)
      Screen.Point(CENTER_OFFSET_X - 1, CENTER_OFFSET_Y, ARROW_COLOR)
      Screen.Point(CENTER_OFFSET_X, CENTER_OFFSET_Y - 1, ARROW_COLOR)
      Screen.Draw()        
    DisplayLock.release()
    time.sleep(DISPLAY_EXPIRATION_CYCLE)

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

  session = udp2led(**opts)

  while True:
    session.process()


