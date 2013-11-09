// -*- C++ -*-
/*
  RainbowduinoSlave - Rainbowduino Slave using Rainbowduino Library for Arduino
  Copyright (c) 2011 Sam C. Lin lincomatic@hotmail.com ALL RIGHTS RESERVED

  plasma code based on  Color cycling plasma   
    Version 0.1 - 8 July 2009
    Copyright (c) 2009 Ben Combee.  All right reserved.
    Copyright (c) 2009 Ken Corey.  All right reserved.
    Copyright (c) 2008 Windell H. Oskay.  All right reserved.

  RainbowduinoSlave is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public
  License as published by the Free Software Foundation; either
  version 2.1 of the License, or (at your option) any later version.

  This demo is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with this library; if not, write to the Free Software
  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
*/

#include "Rainbowduino.h"

#define MSYNC // enable code related to music sync. comment this out if you aren't going to implement music sync

//n.b. couldn't get it to work @ 115200 w/ Duemilanove as serial
//#define BAUD_RATE 57600
#define BAUD_RATE 19200

#define SYNC_BYTE 0xAA // start of packet
// opcodes
#define OPC_START 0x01
#define OPC_PING  0x01
#define OPC_PLAY_FRAME 0x02 // play a 12-bit frame
#define OPC_QUEUE_FRAME 0x03
#define OPC_SET_MODE 0x04
#define OPC_FILL 0x05 // fill with a solid color
#define OPC_END   OPC_FILL

#define CMODE_START 1
#define CMODE_PLASMA 1
#define CMODE_PLAY_FRAME 2
#define CMODE_MUSIC_SYNC 3
#define CMODE_FILL 4
#define CMODE_END CMODE_FILL

byte curMode;
byte curError;
//this should be <= RX_BUFFER_SIZE from HardwareSerial.cpp (128)
#define PKTBUFLEN 100
byte packetBuf[PKTBUFLEN]; // buffer for input

#define RainbowduinoScreenWidth 8
#define RainbowduinoScreenHeight 8

#define PACKED_FRAME_LEN 96 // # bytes in a packed (12-bit) frame

//#define SERIAL_WAIT_TIME_IN_MS 18 //((PKTBUFLEN * 8 * 1000)/ BAUD_RATE)
#define SERIAL_WAIT_TIME_IN_MS 54 //((PKTBUFLEN * 8 * 1000)/ BAUD_RATE)

typedef struct
{
  unsigned char r;
  unsigned char g;
  unsigned char b;
} ColorRGB;

typedef struct pixelRGB {
  unsigned char r;
  unsigned char g;
  unsigned char b;
} PixelRGB;

//a color with 3 components: h, s and v
typedef struct 
{
  unsigned char h;
  unsigned char s;
  unsigned char v;
} ColorHSV;

long paletteShift;


//Converts an HSV color to RGB color
void HSVtoRGB(void *vRGB, void *vHSV) 
{
  float r, g, b, h, s, v; //this function works with floats between 0 and 1
  float f, p, q, t;
  int i;
  ColorRGB *colorRGB=(ColorRGB *)vRGB;
  ColorHSV *colorHSV=(ColorHSV *)vHSV;

  h = (float)(colorHSV->h / 256.0);
  s = (float)(colorHSV->s / 256.0);
  v = (float)(colorHSV->v / 256.0);

  //if saturation is 0, the color is a shade of grey
  if(s == 0.0) {
    b = v;
    g = b;
    r = g;
  }
  //if saturation > 0, more complex calculations are needed
  else
  {
    h *= 6.0; //to bring hue to a number between 0 and 6, better for the calculations
    i = (int)(floor(h)); //e.g. 2.7 becomes 2 and 3.01 becomes 3 or 4.9999 becomes 4
    f = h - i;//the fractional part of h

    p = (float)(v * (1.0 - s));
    q = (float)(v * (1.0 - (s * f)));
    t = (float)(v * (1.0 - (s * (1.0 - f))));

    switch(i)
    {
      case 0: r=v; g=t; b=p; break;
      case 1: r=q; g=v; b=p; break;
      case 2: r=p; g=v; b=t; break;
      case 3: r=p; g=q; b=v; break;
      case 4: r=t; g=p; b=v; break;
      case 5: r=v; g=p; b=q; break;
      default: r = g = b = 0; break;
    }
  }
  colorRGB->r = (int)(r * 255.0);
  colorRGB->g = (int)(g * 255.0);
  colorRGB->b = (int)(b * 255.0);
}

unsigned int RGBtoINT(void *vRGB)
{
  ColorRGB *colorRGB=(ColorRGB *)vRGB;

  return (((unsigned int)colorRGB->r)<<16) + (((unsigned int)colorRGB->g)<<8) + (unsigned int)colorRGB->b;
}


float
dist(float a, float b, float c, float d) 
{
  return sqrt((c-a)*(c-a)+(d-b)*(d-b));
}


void
plasma_morph()
{
  unsigned char x,y;
  float value;
  ColorRGB colorRGB;
  ColorHSV colorHSV;

  for(x = 0; x < RainbowduinoScreenWidth; x++) {
    for(y = 0; y < RainbowduinoScreenHeight; y++)
      {
	value = sin(dist(x + paletteShift, y, 128.0, 128.0) / 8.0)
	  + sin(dist(x, y, 64.0, 64.0) / 8.0)
	  + sin(dist(x, y + paletteShift / 7, 192.0, 64) / 7.0)
	  + sin(dist(x, y, 192.0, 100.0) / 8.0);
	colorHSV.h=(unsigned char)((value) * 128)&0xff;
	colorHSV.s=255; 
	colorHSV.v=255;
	HSVtoRGB(&colorRGB, &colorHSV);
	
	Rb.setPixelXY(x, y, colorRGB.r, colorRGB.g, colorRGB.b);
      }
  }
  paletteShift++;

//  Rb.FlipPage(); // swap screen buffers to show it
}


// unpack 12-bit 8x8 RGB data into current writeable 24-bit frame buffer
// and then show it
// input format packs 4-bit RGB components for 2 adjacent pixels into 3 bytes
// output is 8-bit RGB components
#if 1
void unpackFrame(byte *buf,byte flip=1)
{
  byte r = 0;
  byte bidx = 0;
  PixelRGB p;
  byte *pbuf = buf;
  for (byte y=0;y < RainbowduinoScreenHeight;y++) {
    for (byte x=0;x < RainbowduinoScreenWidth;x+=2) {
      byte b = *(pbuf++);

      p.r = b & 0xf0;
      p.g = b << 4;
      b = *(pbuf++);
      p.b = b & 0xf0;
      Rb.setPixelXY(x, y, p.r, p.g, p.b);
      p.r = b << 4;
      b = *(pbuf++);
      p.g = b & 0xf0;
      p.b = b << 4;
      Rb.setPixelXY(x+1, y, p.r, p.g, p.b);
    }
  }
}
#else
void unpackFrame(byte *buf,byte flip=1)
{
  byte r = 0;
  byte bidx = 0;
  PixelRGB *p = Rb.curWriteFrame;
  byte *pbuf = buf;
  for (byte y=0;y < RainbowduinoScreenHeight;y++) {
    for (byte x=0;x < RainbowduinoScreenWidth/2;x++) {
      byte b = *(pbuf++);

      p->r = b & 0xf0;
      p->g = b << 4;
      b = *(pbuf++);
      p->b = b & 0xf0;
      (++p)->r = b << 4;
      b = *(pbuf++);
      p->g = b & 0xf0;
      p->b = b << 4;
      p++;
    }
  }
  if (flip) {
    Rb.FlipPage();
  }
}
#endif

/* 
   readPacket - read a packet from the host
   packet structure
   BYTE sync byte
   BYTE opcode
   BYTE datalen // max data payload = 255 bytes
   data
   BYTE checksum = sum of the whole packet after the sync byte

   return
     > 0 = number of bytes read
     = 0 = nothing to read
     < 0 = error
*/
int readPacket(byte *pkt)
{
  byte b;
  byte idx = 0;
  byte chksum = 0;
  byte i;
  byte ckr;

  // search input buffer for a sync byte
  idx = -1;
  while (Serial.available() > 0) {
    if (Serial.read() == SYNC_BYTE) {
      idx = 0;
      break;
    }
  }

  if (idx != 0) { // no sync byte found
    return 0;    
  }

  // wait for opcode + datalen
  i = SERIAL_WAIT_TIME_IN_MS;
  while (Serial.available() < 2) {
    delay(1); 
    if (i-- == 0) {
      return -2; // get out if takes too long
    }
  }


  pkt[idx++] = Serial.read(); // opcode
  pkt[idx++] = Serial.read(); // datalen

  if ((pkt[0] < OPC_START) || (pkt[0] > OPC_END)) {
    return -3; // bad opcode
  }

  if (pkt[1] > (PKTBUFLEN-2)) {
    // datalen too big
    return -4;
  }

  // wait for data + chksum
  i = SERIAL_WAIT_TIME_IN_MS;
  while (Serial.available() < pkt[1]+1) {
    delay(1); 
    if (i-- == 0) {
      return -5; // get out if takes too long
    }
  }


  // read the data
  for (i=0;i < pkt[1];i++) {
    b = Serial.read();
    pkt[idx++] = b;
    chksum += b;
  }

  // read chksum
  ckr = Serial.read();
  chksum += pkt[0]+pkt[1]; // add opcode + datalen

  if (ckr != chksum) {
    return -6; // bad chksum
  }
  else {
    return (int)idx; // return number of bytes in packet
  }
}

byte setMode(byte mode) {
  if ((mode >= CMODE_START) && (mode <= CMODE_END)) {
    curMode = mode;
    return 0;
  }
  else {
    return 1;
  }
}

void setup()
{
  Rb.init(); // initialize the board
  curError = 0;

  Serial.begin(BAUD_RATE); //Setup high speed Serial
  Serial.flush();

  
  // compensate for relative intensity differences in R/G/B brightness
  // array of 6-bit base values for RGB (0~63)
  // whiteBalVal[0]=red
  // whiteBalVal[1]=green
  // whiteBalVal[2]=blue
//  unsigned char whiteBalVal[3] = {36,63,63}; // for LEDSEE 6x6cm round matrix
  unsigned char whiteBalVal[3] = {22,63,63}; // for 5cm CA LED
//  Rb.SetWhiteBal(whiteBalVal);

  // plasma
  paletteShift=128000;

  curMode = CMODE_PLASMA;


}


// check for a packet from the host and process it
void readProcessPacket()
{
  //
  // fetch a data packet from host
  //
  int bytesRead = readPacket(packetBuf);

  if (bytesRead) {
    // Serial.write(bytesRead);
    if (bytesRead > 0) { // process packet
      switch(packetBuf[0]) {
      case OPC_PING:
        // NOP
      	break;
      case OPC_PLAY_FRAME: // incoming frame
        //  curMode = CMODE_PLAY_FRAME;
        if (curMode == CMODE_PLAY_FRAME) {
        	if (packetBuf[1] == PACKED_FRAME_LEN) {
        	  unpackFrame(packetBuf + 2);
                  curError = 0;
        	} else {
            curError = 1; // bad data length
          }
        }
        break;

      case OPC_SET_MODE:
        if (!setMode(packetBuf[2])) {
          curError = 0;
        } else {
          curError = 1; // unknown mode
        }
        break;  

      default:
      	// unknown opcode
      	; // fall though
      }
    }
    Serial.write(curError); // send current error code to host
  }
}

void loop()
{
  // check for packet from host and process
  readProcessPacket();

  if (curMode == CMODE_PLASMA) {
    plasma_morph();
  }
}
