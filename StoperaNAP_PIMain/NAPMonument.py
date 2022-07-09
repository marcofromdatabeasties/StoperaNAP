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
        GPIO.setup(constants.PUMP_IJMUIDEN, GPIO.OUT)
        GPIO.setup(constants.PUMP_VLISSINGEN, GPIO.OUT)
        GPIO.setup(constants.VL_IJMUIDEN, GPIO.OUT)
        GPIO.setup(constants.VL_VLISSINGEN, GPIO.OUT)
        
        GPIO.output(constants.VL_IJMUIDEN, GPIO.HIGH)
        GPIO.output(constants.VL_VLISSINGEN, GPIO.HIGH)
        #GPIO.output(constants.VL_53, GPIO.HIGH)
        
        GPIO.output(constants.PUMP_IJMUIDEN, GPIO.LOW)
        GPIO.output(constants.PUMP_VLISSINGEN, GPIO.LOW)
        GPIO.output(constants.PUMP_53, GPIO.LOW)
        
        
        GPIO.setup(constants.BTN_SHUTDOWN, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(constants.BTN_EMPTY, GPIO.IN, GPIO.PUD_UP) 
        GPIO.setup(constants.BTN_NAP, GPIO.IN, GPIO.PUD_UP) 
        
        self.screen = LCD()
       
    def start(self):
        self.IJmuiden = WaterColumn(constants.COLUMN_1_LOCATION, constants.PR_IJMUIDEN
                                    , constants.VL_IJMUIDEN, constants.PUMP_IJMUIDEN) 
        self.Vlissingen = WaterColumn(constants.COLUMN_2_LOCATION, constants.PR_VLISSINGEN, constants.VL_VLISSINGEN,constants.PUMP_VLISSINGEN)
        #self.Watersnood = WaterColumn1953("1953", 2, 20, 21)

        ijmuidenthread = threading.Thread(target=self.IJmuiden.runWorlds, args=(self.screen,), daemon=True)
        vlissingenthread = threading.Thread(target=self.Vlissingen.runWorlds, args=(self.screen,), daemon=True)
        ijmuidenthread.start()
        vlissingenthread.start()

        while True:
            self.buttonTesting()
            time.sleep(0.1)
           
    #obsolete function in case of interrupt troubles on-site
    def buttonTesting(self):
        if GPIO.input(constants.BTN_SHUTDOWN) == GPIO.HIGH:
            self.shutdown_h_now()
        
        if GPIO.input(constants.BTN_NAP == GPIO.HIGH):
            self.setNAPToZeroOrNot()
        else:
            self.Vlissingen.setToNormal()
            self.IJmuiden.setToNormal()
        
        if GPIO.input(constants.BTN_EMPTY) == GPIO.HIGH:
            self.setNAPToEmptyOrNot()
        else:
            self.Vlissingen.setToNormal()
            self.IJmuiden.setToNormal()

    def shutdown_h_now(self, channel):
        time.sleep(0.05)
        GPIO.cleanup()
        self.screen.clear()
        self.screen.writeInfoToScreen("Shutdown...")
        os.system("sudo shutdown -h now")
        time.sleep(5)
        self.screen.writeInfoToScreen("Bye...")
            
    def setNAPToZeroOrNot(self):
            self.IJmuiden.setLevelToZero()
            self.Vlissingen.setLevelToZero()
            
    def setNAPToEmptyOrNot(self):
            self.IJmuiden.setLevelToEmpty()
            self.Vlissingen.setLevelToEmpty()
    