import serial
import struct

class Colorduino:
  "Colorduino device driver."
  def __init__(self, tty):
    self.port = serial.Serial(tty, 19200, timeout=1)
    self.Clear()

  def Clear(self):
    "Clear everything."
    self.display  = []
    self.display += [ 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]
    self.display += [ 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]
    self.display += [ 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]
    self.display += [ 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]
    self.display += [ 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]
    self.display += [ 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]
    self.display += [ 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]
    self.display += [ 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]

  def Point(self, x, y, c):
    "Display a dot."
    self.display[ x + y * 8 ] = c

  def Draw(self):
    "Refresh the screen."

    frame = []
    frame += [ 0xaa ]
    frame += [ 0x04 ]
    frame += [ 1 ]
    frame += [ 2 ]
    
    csum = 0
    for c in frame[1:len(frame)]:
      csum += c
    
    frame += [ csum & 0xFF ]
    
    #print frame
    
    pkt=struct.pack('B'*len(frame),*frame)
    
    self.port.write(pkt)
    
    rval = self.port.read(1)
    
    #toHex = lambda x:"".join([hex(ord(c))[2:].zfill(2) for c in x])
    #print toHex(rval)
    
    frame  = []
    frame += [ 0xaa ]
    frame += [ 0x02 ]
    frame += [ 96 ]
    
    rest = 0
    for i in range(len(self.display)):
      pixel = self.display[i]
      r = (pixel >> 16)
      g = (pixel >> 8) & 0xFF
      b = pixel & 0xFF
      r4 = r >> 4
      g4 = g >> 4
      b4 = b >> 4
      if ((i & 1) == 0):
        frame += [(r4 << 4) | g4]
        rest = b4
      else:
        frame += [(rest << 4) | r4]
        frame += [(g4 << 4) | b4]
    
    csum = 0
    for c in frame[1:len(frame)]:
      csum += c
    
    frame += [ csum & 0xFF ]
    
    #print frame
    
    pkt=struct.pack('B'*len(frame),*frame)
    
    self.port.write(pkt)
    
    #rval = self.port.read(1)
    #print toHex(rval)


#ser.close()

