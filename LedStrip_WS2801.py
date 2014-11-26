# Simple Python Library for accessing WS2801 LED stripes
# Copyright (C) 2014 Ian Smith <ian@astounding.org.uk>
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# 
#
# This code is a development of GPLv2 code by Philipp Tiefenbacher
# <wizards23@gmail.com> For information about the original code and
# hardware it was written for please visit:
# http://www.hackerspaceshop.com/ledstrips/raspberrypi-ws2801.html
#
# 
#
# Notes
# =====
# 
# This code does not explicitly implement the necessary pause after
# uploading a stream of data to the LED chain.  The WS2801 chips need
# 500uS with no clock pulses to signal the end of the current stream
# of data.  This library just assumes you'll spend at least 500uS
# doing something else before you do another update() call.  In
# practice, (on a Raspberry Pi at least) I don't think you can get
# back to the update routine faster than that even if you wanted to,
# so it's not a problem.
#
# This library generally defaults to holding the colour values as
# floats, even though the WS2801 chips only want each colour component
# as an unsigned 8-bit number.  This is so that small fade values work
# properly at low brightness.
# That is, suppose you have brightness 3 and want to fade it by 10% on
# each refresh:
# As floats:
# 3.00 -> 2.70 transmit 2
#      -> 2.43 transmit 2
#      -> 2.19 transmit 2
#      -> 1.96 transmit 1
#      -> 1.77 transmit 1
#      etc. the eleventh refresh gives 0.98 transmit 0
# As integer:
# 3 -> 2 transmit 2
#   -> 1 transmit 1
#   -> 0 transmit 0
#   -> 0 transmit 0
#   -> 0 transmit 0
# Rather than dropping below a third of the starting intensity after
# ten refreshes, as you should going 0.9 per refresh, you get there
# after two.
# Obviously, that makes this slower than an integer implementation,
# but this will still fade a 50-pixel string at over 200Hz refresh on
# Raspberry Pi.
#
# There is potential for odd effects with teh rotate function in teh
# case of a configuration where some rows have fewer pixels than
# others.  For example, suppose one row has 6 and anotehr row has 12.
# With one step of rotation, teh first pixel on teh row of six rotates
# halfway towards teh next.  by normal rules of rounding, that casues
# teh pixels in teh row of 6 to advance one step.  If you call
# rotate(1) again, they will again advance, and end up advancing twice
# as fast as teh row of 12.

# To overcome this if you want multiple sequential rotates, initialise
# with two buffers - a 'working' and a 'spare'.  Then, rather than n
# sequential rotate(1), you copy spare to working and do rotate(n) for
# teh nth step.  
# That is, do not do this:
#     for n in range(0,99):
#         rotate(1)
#         update()
# Do this instead:
#     copyBuffer(0,1)
#     for n in range(0,99)
#         copyBuffer(1,0)
#         rotate(n+1)
#         update() 

import spidev
from decimal import *

# access to SPI with python spidev library
class LedStrip_WS2801:  
    def __init__(self, nLeds, nBuffers=1):
        # embed our version 
        self.version=20140111.01
        
        # create spi object
        self.spi = spidev.SpiDev() 
        
        self.spi.open(0, 1)
        # actually, my hardware ignores chip select so either
        # device works your hardware might be better
        # implemented than mine
        
        self.spi.max_speed_hz = 2000000 
        # SPI goes faster, WS2801 datasheet states max clock
        # freq 25MHz but then has statement "output stage with
        # strong driving capability which enables the data and
        # clock can be transmitted up to 6 meters at 2MHz
        # clock frequency"
        # 2MHz clock theoretically allows a 750 LED chain to
        # refresh at 100Hz with a bit of margin, so this is
        # probably adequate

        # force nLeds to be a list (if necesary, of one element)
        if isinstance(nLeds,list):
            pass
        else:
            nLeds=[nLeds]
        self.nLeds=nLeds

        # the mappings between the 1D list and 2D grid
        self.rows=len(nLeds)
        self.cols=max(nLeds)
        self.gridm=[] # from 2D grid to 1D list
        self.listm=[] # from 1D list to 2D grid
        for r in range(sum(nLeds)):
            # need an initial empty listm
            self.listm.append([])
        for r in range(0,self.rows):
            gridm_row=[]
            for c in range(0,self.cols):
                # determine which pixel a particular
                # row,column in teh grid would map to
                pixel = int((Decimal(c)/self.cols*nLeds[r]).to_integral_value()%nLeds[r]+sum(nLeds[:r]))
                # in listm we record all teh row,col
                # that map to a particular pixel
                self.listm[pixel].append([r,c])
                # in gridm there's only one pixel for each grid position
                gridm_row.append(pixel)
            self.gridm.append(gridm_row)
            
        # create our buffers from the template
        self.nBuffers = nBuffers
        self.buffers = []
        for i in range(0, nBuffers):
            ba=[]
            for l in range(0, sum(nLeds)):
                ba.extend([0.,0.,0.])
                # see note at start of file for
                # discussion of why floats
                self.buffers.append(ba)

    def close(self):
        if (self.spi != None):
            self.spi.close()
            self.spi = None

    # send specified buffer to led chain
    def update(self, bufferNr=0):
        self.spi.writebytes([int(x) for x in self.buffers[bufferNr]])
        # note conversion of possible floats in buffer to ints

    # set one specified pixel to a single colour 
    # (by default first pixel full power white)
    def setPixel(self, index=0, colour=[255.,255.,255.], bufferNr=0):
        # if index is a list, assume that it is a 2D grid
        # position so we need to turn it into teh relevant 1D
        # position
        if isinstance(index,list):
            index = self.gridm[index[0]][index[1]]
        # now update in the list buffer 
        self.buffers[bufferNr][index*3:index*3+3] = (colour[0], colour[1], colour[2])

    # instantaneously set all pixels to a single colour 
    # (by default full power white)
    def setAll(self, colour=[255.,255.,255.], bufferNr=0):
        self.buffers[bufferNr]=[]
        for i in range(0, sum(self.nLeds)):
            self.buffers[bufferNr].extend(colour)

    # copy the value of one pixel to another pixel
    def copyPixel(self, fromP, toP, bufferNr=0):
        # if indexes are lists, assume that it's a 2D grid
        # position so we need to turn it into teh relevant 1D
        # position
        if isinstance(fromP,list):
            fromP = self.gridm[fromP[0]][fromP[1]]
        if isinstance(toP,list):
            toP = self.gridm[toP[0]][toP[1]]
        # as an aside:
        # I tried  try:
        #               fromP = self.gridm[fromP[0]][fromP[1]]
        #          except TypeError:
        #                pass
        # when fromP is a list, that code runs a little faster
        # (typically, 15% faster) than using 'isinstance', but
        # when fromP is an int, it takes three times as long
        # as the 'isinstance' code, so I'm sticking with that,
        # even though some people think type checking in
        # advance is less 'pythonic'
        c=self.buffers[bufferNr][fromP*3:fromP*3+3]
        self.setPixel(toP, c, bufferNr)

    # copy one whole linear buffer to another
    def copyBuffer(self, fromB, toB):
        self.buffers[toB]=self.buffers[fromB]

    # fade one specified pixel towards a single colour 
    # (by default first pixel towards off - note opposite default

    # to setPixel)
    # proportion should be an absolute fraction, eg 0.05 but if it
    # is >=1 will be treated as a percentage thus
    # fadePixel(0,0.05) and fadePixel(0,5) will have same effect
    # positive p fades that far from start towards target colour,
    # ie fadePixel(0,0.05) gives a pixel at 95% of previous
    # intensity 
    # negative p fades to that value from target colour ie
    # fadePixel(0,-0.05) gives a pixel at 5% of previous intensity
    def fadePixel(self, index=0, proportion=0.1, colour=[0.,0.,0.], bufferNr=0):
        # if index is a list, assume that it's a 2D grid
        # position so we need to turn it into teh relevant 1D
        # position
        if isinstance(index,list):
            index = self.gridm[index[0]][index[1]]
        # if magnitude of proportion is greater than 1, assume
        # it's a percentage and convert it to a fractional
        # value
        if abs(proportion) < 1:
            p = float(proportion)
        else:
            p = proportion / 100.0
        # if teh proportion value is negative convert it from
        # the distance from target to the distance from start
        # colour
        if p < 0.0:
            p = 1.0+p
        c=self.buffers[bufferNr][index*3:index*3+3]
        for j in range(0,3):
            c[j]=c[j]+p*(colour[j]-c[j])
        self.setPixel(index, c, bufferNr) 

    # fade all pixels towards a single colour (by default to off -
    # note is opposite of setAll) implemented independent of
    # fadePixel() to avoid recalculating p for every pixel
    def fadeAll(self, proportion=0.1, colour=[0.,0.,0.], bufferNr=0):
        if abs(proportion) < 1:
            p = float(proportion)
        else:
            p = proportion / 100.0
        if p < 0.0:
            p = 1.0+p
        for i in range(0, sum(self.nLeds)):
            c=self.buffers[bufferNr][i*3:i*3+3]
            for j in range(0,3):
                c[j]=c[j]+p*(colour[j]-c[j])
            self.setPixel(i, c, bufferNr) 

    # rotate about the polar axis
    # steps is in units of teh spacing between pixels in teh row
    # with most pixels
    # Note this is clockwise when looking down on teh north pole
    # (where north pole is defied as teh one which teh first ring
    # of LEDs is around).  That's a negative rotation in normal
    # vector sense (ie, +ve rotation about the vector from centre
    # to teh north pole would rotate teh other way).  However,
    # this sign convention, while less maths-y is more like what
    # is probably expected
    def rotate(self, steps=1, bufferNr=0):
        steps = steps % self.cols
        # fill in the grid with colours from the buffer
        grid=[]
        for r in range(self.rows):
            g_row=[]
            for p in self.gridm[r]:
                g_row.append(self.buffers[bufferNr][p*3:p*3+3])
            # now do the rotate on this row into a grid
            grid.append(g_row[(0-steps):]+g_row[:(0-steps)])
        # now populate the linear buffer by working through listm
        self.buffers[bufferNr]=[]
        for r in self.listm:
            self.buffers[bufferNr].extend(grid[r[0][0]][r[0][1]])

                
