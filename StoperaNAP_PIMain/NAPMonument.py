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
import os

class NAPMonument:
     
    def __init__(self):
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
        GPIO.setup(13, GPIO.IN) #reboot
        
        GPIO.output(12, GPIO.HIGH)
        
        #GPIO.add_event_detect(13, GPIO.FALLING, callback=self.shutdown_h_now, bouncetime=200)
        #GPIO.add_event_detect(16, GPIO.FALLING, callback=self.shutdown_h_now, bouncetime=200)
        #GPIO.add_event_detect(5, GPIO.BOTH, callback=self.setNAPToZeroOrNot, bouncetime=200)
        #GPIO.add_event_detect(6, GPIO.BOTH, callback=self.setNAPToEmptyOrNot, bouncetime=200)
        
        self.screen = LCD()
       
    def start(self):
        self.IJmuiden = WaterColumn(constants.COLUMN_1_LOCATION, 0, 17, 27) #12 is in use by MCP3208
        self.Vlissingen = WaterColumn(constants.COLUMN_2_LOCATION, 1, 23, 24)
        #self.Watersnood = WaterColumn1953("1953", 2, 20, 21)

        ijmuidenthread = threading.Thread(target=self.IJmuiden.runWorlds, args=(self.screen,), daemon=True)
        vlissingenthread = threading.Thread(target=self.Vlissingen.runWorlds, args=(self.screen,), daemon=True)
        ijmuidenthread.start()
        vlissingenthread.start()

        while True:
            #self.buttonTesting()
            time.sleep(60)
           
    #obsolete function in case of interrupt troubles on-site
    def buttonTesting(self):
        if (GPIO.input(13) or GPIO.input(16)):
            self.shutdown_h_now(16)
        if (GPIO.input(5)):
            self.setNAPToZeroOrNot(5)
        if(GPIO.input(5)):
            self.setNAPToEmptyOrNot (6)


    def shutdown_h_now(self, channel):
        time.sleep(0.05)
        if (not GPIO.input(channel)) and (channel == 13 or channel == 16): 
            self.screen.writeInfoToScreen("Shutdown...")
            time.sleep(5)
            os.system("sudo shutdown -h now")
            
    def setNAPToZeroOrNot(self, channel):
        self.Vlissingen.setToNormal() #erase previous state
        if (not GPIO.input(channel)):
            self.IJmuiden.setLevelToZero()
            self.Vlissingen.setLevelToZero()
        else:
            self.Vlissingen.setToNormal()
            
    def setNAPToEmptyOrNot(self, channel):
        self.Vlissingen.setToNormal() #erase previous state
        if (not GPIO.input(channel)):
            self.IJmuiden.setLevelToEmpty()
            self.Vlissingen.setLevelToEmpty()
        else:
            self.Vlissingen.setToNormal()
    