#!/usr/bin/python

import time
import colorsys

from LedStrip_WS2801 import *

# hue of first LED in the chain at any moment
hue=0.    

# amount each LED differs from the previous in the chain
delta_n_hue=0.001

# amount the colour changes each second
delta_t_hue=1./120

# number of LEDs on teh chain
nLEDs=125

# create ledstrip object
l = LedStrip_WS2801(nLEDs)

n=0
while 1:
    for n in range (nLEDs):
        x=colorsys.hls_to_rgb(((hue+n*delta_n_hue)%1.0),0.1,1)
        colour=[255*x[0], 255*x[1], 255*x[2]]
        # set pixel n
        l.setPixel(n,colour)

    # send that data out    
    l.update()

    # wait to next frame
    time.sleep(0.1)
    hue = hue + delta_t_hue/10.
