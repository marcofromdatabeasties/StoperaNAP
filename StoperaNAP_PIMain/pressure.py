#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 16:37:42 2021

@author: ubuntu
"""
import ADS1x15

#https://github.com/chandrawi/ADS1x15-ADC
#deze moet anders

class PressureSensor:
    
    def __init__(self):
        self.ADS = ADS1x15.ADS1115(1, 0x48)
        self.ADS.setGain(self.ADS.PGA_4_096V)
    
    def getColumnLevel(self, channel):    
        raw = self.ADS.readADC(0) 
        value = self.ADS.toVoltage(raw)

        #4mA minimal current of pressure sensor (gets 0.8v ).
        #30mA max current is 4v
        return (value * 3.25 -2.59)

    
if __name__ == "__main__":
    pressure = PressureSensor()
    print(pressure.getColumnLevel(0))
        