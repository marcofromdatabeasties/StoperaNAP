#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 16:37:42 2021

@author: ubuntu
"""

import threading
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


class PressureSensor:
    
    def __init__(self):
        self.lock = threading.Lock()
        self.i2c = busio.I2C(board.SCL, board.SDA)  
        self.ads = ADS.ADS1115(self.i2c)
        self.ads.mode = ADS.Mode.SINGLE
    
    def getColumnLevel(self, channel):

        value = AnalogIn(self.ads, channel).voltage       

        #4mA minimal current of pressure sensor (gets 0.8v ).
        #20mA max current is 4v
        return (value * 3.25 -2.59)
    
    
if __name__ == "__main__":
    pressure = PressureSensor()
    print(pressure.getColumnLevel(ADS.P1))
        