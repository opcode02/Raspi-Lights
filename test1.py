#!/usr/bin/python

import time
import itertools

from LedStrip_WS2801 import *

nLeds = 138

Red = [0xFF, 0, 0]
Green = [0, 0xFF, 0]
Blue = [0, 0, 0xFF]
#Orange = [0xFF, 0x66, 0]
Orange = [0xCC, 0x33, 0]
#Violet = [0xCC, 0, 0xCC]
Violet = [0x3F, 0, 0x3F] # For a darker purple linearly decrease red and blue

# create ledstrip object
l = LedStrip_WS2801(nLeds, 2)

toggle = itertools.cycle([Red, Orange, Green, Blue, Violet]).next

for pixel in range(0, nLeds):    
    color = toggle()
    l.setPixel(pixel, color)

l.update()

while 1:
    l.copyBuffer(0, 1)
    for n in range(0,100):
        l.copyBuffer(1, 0)
        l.rotate(n+1) 
        l.update()
        time.sleep(0.5)
