// -*- C++ -*-
/*
  ColorduinoSlave - Colorduino Slave using Colorduino Library for Arduino
  Copyright (c) 2011 Sam C. Lin lincomatic@hotmail.com ALL RIGHTS RESERVED

  plasma code based on  Color cycling plasma   
    Version 0.1 - 8 July 2009
    Copyright (c) 2009 Ben Combee.  All right reserved.
    Copyright (c) 2009 Ken Corey.  All right reserved.
    Copyright (c) 2008 Windell H. Oskay.  All right reserved.

  ColorduinoSlave is free software; you can redistribute it and/or
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

#include <Colorduino.h>

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


#ifdef MSYNC
#define SENSOR_PIN A4 //SDA // analog input pin for music
//#define SENSOR_PIN A5 //SCL // analog input pin for music

// trigger next frame when music amplitude > threshold
// increase threshold to decrease sensitivity
// decrease threshold to increase sensitivity
byte threshold = 31;
// debouncing - filter out consecutive triggers that are too close
// together to slow down the animation.  decrease this value
// to make it more sensitive to shorter beat intervals
int minBeatInterval = 750;

byte threshCrossed = 0;
#endif // MSYNC


#define PACKED_FRAME_LEN 96 // # bytes in a packed (12-bit) frame
//ATmega168's meager memory only allows us queue 2 frames
// can be bigger for 328
#define PACKED_FRAME_QUEUE_LEN 2 // number of frames we can buffer

// ring buffer (FIFO) for packed frames
class PackedFrameQueue {
  byte frameQueue[PACKED_FRAME_QUEUE_LEN][PACKED_FRAME_LEN];
  byte frameCnt;
  byte firstFrameIdx;
  byte addFrameIdx;
public:
  PackedFrameQueue();
  
  byte *dequeueFrame();
  byte addFrame(byte *frame);
  void empty() {
    frameCnt = 0;
    firstFrameIdx = 0;
    addFrameIdx = 0;
  }
  byte isFull() { return ((frameCnt == PACKED_FRAME_QUEUE_LEN) ? 1 : 0); }
  byte getFrameCnt() { return frameCnt; }
};


PackedFrameQueue packedFrameQueue;

PackedFrameQueue::PackedFrameQueue()
{
  empty();
}

// dequeue and return a frame
byte *PackedFrameQueue::dequeueFrame()
{
  if (frameCnt) {
    frameCnt--;
    byte *frame = frameQueue[firstFrameIdx];
    if (!frameCnt) {
      firstFrameIdx = 0;
      addFrameIdx = 0;
    }
    else {
      if (++firstFrameIdx == PACKED_FRAME_QUEUE_LEN) {
        // wrap
        firstFrameIdx = 0;
      }
    }
    return frame;
  }
  else {
    // empty queue
    return NULL;
  }
}


// return 1 on queue full
//        0 on success
byte PackedFrameQueue::addFrame(byte *frame)
{
  if (frameCnt < PACKED_FRAME_QUEUE_LEN) {
    frameCnt++;
    byte *b = frameQueue[addFrameIdx];
    if (++addFrameIdx == PACKED_FRAME_QUEUE_LEN) {
      addFrameIdx = 0;
    }
    for (byte i=0;i < PACKED_FRAME_LEN;i++) {
     // *(b++) = *(frame++);
     b[i]=frame[i];
    }
    return 0;
  }
  else {
    // queue full, return error
    return 1;
  }
}

//#define SERIAL_WAIT_TIME_IN_MS 18 //((PKTBUFLEN * 8 * 1000)/ BAUD_RATE)
#define SERIAL_WAIT_TIME_IN_MS 54 //((PKTBUFLEN * 8 * 1000)/ BAUD_RATE)

typedef struct
{
  unsigned char r;
  unsigned char g;
  unsigned char b;
} ColorRGB;

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

  for(x = 0; x < ColorduinoScreenWidth; x++) {
    for(y = 0; y < ColorduinoScreenHeight; y++)
      {
	value = sin(dist(x + paletteShift, y, 128.0, 128.0) / 8.0)
	  + sin(dist(x, y, 64.0, 64.0) / 8.0)
	  + sin(dist(x, y + paletteShift / 7, 192.0, 64) / 7.0)
	  + sin(dist(x, y, 192.0, 100.0) / 8.0);
	colorHSV.h=(unsigned char)((value) * 128)&0xff;
	colorHSV.s=255; 
	colorHSV.v=255;
	HSVtoRGB(&colorRGB, &colorHSV);
	
	Colorduino.SetPixel(x, y, colorRGB.r, colorRGB.g, colorRGB.b);
      }
  }
  paletteShift++;

  Colorduino.FlipPage(); // swap screen buffers to show it
}

/********************************************************
Name: ColorFill
Function: Fill the frame with a color
Parameter:R: the value of RED.   Range:RED 0~255
          G: the value of GREEN. Range:RED 0~255
          B: the value of BLUE.  Range:RED 0~255
********************************************************/
void ColorFill(unsigned char R,unsigned char G,unsigned char B)
{
  unsigned char i,j;
  
  for (i = 0;i<ColorduinoScreenWidth;i++) {
    for(j = 0;j<ColorduinoScreenHeight;j++) {
      PixelRGB *p = Colorduino.GetPixel(i,j);
      p->r = R;
      p->g = G;
      p->b = B;
    }
  }
  
  Colorduino.FlipPage();
}





// unpack 12-bit 8x8 RGB data into current writeable 24-bit frame buffer
// and then show it
// input format packs 4-bit RGB components for 2 adjacent pixels into 3 bytes
// output is 8-bit RGB components
void unpackFrame(byte *buf,byte flip=1)
{
  byte r = 0;
  byte bidx = 0;
  PixelRGB *p = Colorduino.curWriteFrame;
  byte *pbuf = buf;
  for (byte y=0;y < ColorduinoScreenHeight;y++) {
    for (byte x=0;x < ColorduinoScreenWidth/2;x++) {
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
    Colorduino.FlipPage();
  }
}




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
#ifdef MSYNC
    if (mode == CMODE_MUSIC_SYNC) {
      threshCrossed = 0;
    }
#endif // MSYNC
    return 0;
  }
  else {
    return 1;
  }
}

void setup()
{
  Colorduino.Init(); // initialize the board
  curError = 0;

  Serial.begin(BAUD_RATE); //Setup high speed Serial
  Serial.flush();

#ifdef MSYNC
  pinMode(SENSOR_PIN,INPUT);
#endif // MSYNC

  
  // compensate for relative intensity differences in R/G/B brightness
  // array of 6-bit base values for RGB (0~63)
  // whiteBalVal[0]=red
  // whiteBalVal[1]=green
  // whiteBalVal[2]=blue
//  unsigned char whiteBalVal[3] = {36,63,63}; // for LEDSEE 6x6cm round matrix
  unsigned char whiteBalVal[3] = {22,63,63}; // for 5cm CA LED
  Colorduino.SetWhiteBal(whiteBalVal);

  // plasma
  paletteShift=128000;
  


  // Colorduino.SetPixel(0,0,255,0,0); //r
 // Colorduino.SetPixel(7,0,0,255,0); //g
 // Colorduino.SetPixel(0,7,0,0,255);//b
//  Colorduino.SetPixel(7,7,255,255,255);
  //  Colorduino.FlipPage();

  curMode = CMODE_PLASMA;
 /* 
  int i;
  int j=255;
  for (i=0;i < 8;i++) {
    Colorduino.SetPixel(0,i,j,j,j);
    Serial.println(j);
    j /= 2;
  }
  j=1;
  for (i=0;i < 8;i++) {
    int k=j << 4;
    Colorduino.SetPixel(1,i,k,k,k);
    Serial.println(k);
    j+=2;
  }
  Colorduino.FlipPage();
  */

//ColorFill(255,0,0);
//ColorFill(0,255,0);
//ColorFill(0,0,255);
//ColorFill(255,255,255);
}


// check for a packet from the host and process it
void readProcessPacket()
{
  //
  // fetch a data packet from host
  //
  int bytesRead = readPacket(packetBuf);

 if (bytesRead) {
   //Serial.write(bytesRead);
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
	}
        else {
          curError = 1; // bad data length
        }
      }
	break;

      case OPC_QUEUE_FRAME: // incoming frame
	if (packetBuf[1] == PACKED_FRAME_LEN) {
	  if (!packedFrameQueue.addFrame(packetBuf + 2)) {
            //success
	    curError = 0;
	  }
          else {
            curError = 1; // bad frame
          }
	  if ((curMode == CMODE_MUSIC_SYNC) && packedFrameQueue.isFull()) {
            return;
	  }
	}
        else {
          curError = 1; // bad data length
        }
	break;

      case OPC_SET_MODE:
        if (!setMode(packetBuf[2])) {
          curError = 0;
        }
        else {
          curError = 1; // unknown mode
        }
        break;  
      case OPC_FILL:
	if (curMode == CMODE_FILL) {
	  ColorFill(packetBuf[2],packetBuf[3],packetBuf[4]);
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

#ifdef MSYNC
void doMusicSync()
{
  static int cnt = 32768;
  // read the value from the sensor:
  int sensorValue =  analogRead(SENSOR_PIN);
  
  cnt++;
  if (sensorValue > threshold) {
    //Serial.print(sensorValue);Serial.print(" ");
    if (!threshCrossed && (cnt > minBeatInterval) ) {
      // send ack back to host to fetch next frame
      Serial.write((byte)0);

      threshCrossed = 1;
      cnt = 0;
      
      Colorduino.FlipPage();
    }
  }
  else { // below threshold
    if (threshCrossed) {
      threshCrossed = 0;
      byte *frame = packedFrameQueue.dequeueFrame();
      if (frame) {
	unpackFrame(frame,0);
      }
    }
  }
}
#endif // MSYNC

void loop()
{
  // check for packet from host and process
  readProcessPacket();

  if (curMode == CMODE_PLASMA) {
    plasma_morph();
  }
#ifdef MSYNC  
  else if (curMode == CMODE_MUSIC_SYNC) {
    doMusicSync();
  }
#endif // MSYNC
}
