#!/usr/bin/python

import time
import itertools

from LedStrip_WS2801 import *

nLeds = 138

Red = [255, 0, 0]
Green = [0, 255, 0]
Blue = [0, 0, 255]

# create ledstrip object
l = LedStrip_WS2801(nLeds, 2)

toggle = itertools.cycle([Red, Green, Blue]).next

for pixel in range(0, nLeds):    
    color = toggle()
    l.setPixel(pixel, color)
    l.update()

while 1:
    l.copyBuffer(0, 1)
    for n in range(0,99):
        l.copyBuffer(1, 0)
        l.rotate(n+1) 
        l.update()
        time.sleep(0.5)
