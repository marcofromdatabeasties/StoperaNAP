#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 16:37:42 2021

@author: ubuntu
"""

import threading
import spidev
import RPi.GPIO as GPIO


class Pressure:
    
    def __init__(self):
        self.lock = threading.Lock()
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        self.spi.max_speed_hz=1000000
        
        
    #same thing but for the 12-bit MCP3208
    def readChannel3208(self, channel):
        adc = self.spi.xfer2([6|(channel>>2),channel<<6,0]) #0000011x,xx000000,00000000
        data = ((adc[1]&15) << 8) + adc[2]
        return data
    
    
    def getWaterLevel(self, channel):
        self.lock.acquire(True, 10)
        
        GPIO.output(12, GPIO.LOW)
        value = self.ReadChannel3208(channel)
        GPIO.output(12, GPIO.HIGH)
        
        self.lock.release()
        return 10 * ((value - 744) / 4095) #4mA minimal current of pressure sensor (gets 0.6v = 744).