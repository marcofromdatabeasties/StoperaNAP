#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:25:34 2021

@author: ubuntu

Main class that symbolizes the monument, containing three cylinders two of which 
display the current water level at IJmuiden en Zierikzee and one displaying the
level of the 1953 flood.
"""
import threading
from water import WaterColumn
import time
import RPi.GPIO as GPIO
from screen import LCD
import constants

class NAPMonument:
     
    def __init__(self):
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM) 
        GPIO.setwarnings(True)
        GPIO.setup(17, GPIO.OUT)
        GPIO.setup(27, GPIO.OUT)
        GPIO.setup(23, GPIO.OUT)
        GPIO.setup(24, GPIO.OUT)
        GPIO.setup(20, GPIO.OUT)
        GPIO.setup(21, GPIO.OUT)
        GPIO.setup(12, GPIO.OUT)
        
        GPIO.setup(5, GPIO.IN) # Test
        GPIO.setup(6, GPIO.IN) # Empty
        GPIO.setup(16, GPIO.IN) # Power
        
        self.screen = LCD()
        
        self.IJmuiden = WaterColumn(constants.COLUMN_1_LOCATION, 0, 17, 27) #12 is in use by MCP3208
        self.Vlissingen = WaterColumn(constants.COLUMN_2_LOCATION, 1, 23, 24)
        #self.Watersnood = WaterColumn1953("1953", 2, 20, 21)

        ijmuidenthread = threading.Thread(target=self.IJmuiden.runWorlds, args=(self.screen,), daemon=True)
        vlissingenthread = threading.Thread(target=self.Vlissingen.runWorlds, args=(self.screen,), daemon=True)
        ijmuidenthread.start()
        vlissingenthread.start()
       
    def start(self):
       while True:
           time.sleep(60)

    