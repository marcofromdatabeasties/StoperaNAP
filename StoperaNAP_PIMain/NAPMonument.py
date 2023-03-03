#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:25:34 2021

@author: ubuntu

Main class that symbolizes the monument, containing three cylinders two of which 
display the current water level at IJmuiden en Zierikzee and one displaying the
level of the 1953 flood.
"""
from water import WaterColumn, WaterColumn1953
import logging
import time
import RPi.GPIO as GPIO
from screen import LCD
import constants
import os
from pressure import PressureSensor
from waterdata import RWS
import ET

class NAPMonument:
     
    def __init__(self):
        GPIO.setmode(GPIO.BCM) 
        GPIO.setwarnings(True)
        GPIO.setup(constants.PUMP_IJMUIDEN, GPIO.OUT)
        GPIO.setup(constants.PUMP_VLISSINGEN, GPIO.OUT)
        GPIO.setup(constants.PUMP_53, GPIO.OUT)
        GPIO.setup(constants.VL_53, GPIO.OUT)
        GPIO.setup(constants.VL_IJMUIDEN, GPIO.OUT)
        GPIO.setup(constants.VL_VLISSINGEN, GPIO.OUT)
        
        GPIO.output(constants.VL_IJMUIDEN, GPIO.HIGH)
        GPIO.output(constants.VL_VLISSINGEN, GPIO.HIGH)
        GPIO.output(constants.VL_53, GPIO.HIGH)
        
        GPIO.output(constants.PUMP_IJMUIDEN, GPIO.HIGH)
        GPIO.output(constants.PUMP_VLISSINGEN, GPIO.HIGH)
        GPIO.output(constants.PUMP_53, GPIO.HIGH)
        
        
        GPIO.setup(constants.BTN_SHUTDOWN, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(constants.BTN_EMPTY, GPIO.IN, GPIO.PUD_UP) 
        GPIO.setup(constants.BTN_NAP, GPIO.IN, GPIO.PUD_UP) 
        
        self.screen = LCD()
        time.sleep(1)
        self.screen.clear()
        self.screen.writeInfoToScreen("Hello!")
        self.pressureSensor = PressureSensor()
        self.rws = RWS()
       
    def start(self):
        self.IJmuiden = WaterColumn(constants.COLUMN_1_LOCATION, constants.PR_IJMUIDEN
                                    , constants.VL_IJMUIDEN, constants.PUMP_IJMUIDEN
                                    , self.pressureSensor, self.screen, self.rws, 0) 
        
        self.Vlissingen = WaterColumn(constants.COLUMN_2_LOCATION, constants.PR_VLISSINGEN,
                                      constants.VL_VLISSINGEN,constants.PUMP_VLISSINGEN
                                      , self.pressureSensor, self.screen, self.rws, 1)
        
        self.Watersnood = WaterColumn1953(constants.COLUMN_3_LOCATION, constants.PR_53,
                                      constants.VL_53,constants.PUMP_53
                                      , self.pressureSensor, self.screen, self.rws, 2)


        
        while True:
            try:
                self.buttonTesting()
                self.IJmuiden.runWorlds()
                time.sleep(constants.COLUMN_WAIT)
            except Exception as e:
                logging.error("%s", self.IJmuidenden.measure_location + str(e))
                ET.phoneHome(str(e))
                traceback.print_exc(file=sys.stdout)
            try:
                self.Vlissingen.runWorlds()
                time.sleep(constants.COLUMN_WAIT)
            except Exception as e:
                logging.error("%s", self.Vlissingen.measure_location + str(e))
                ET.phoneHome(str(e))
                traceback.print_exc(file=sys.stdout)
            try:    
                self.Watersnood.runWorlds()
                time.sleep(constants.COLUMN_WAIT)
            except Exception as e:
                logging.error("%s", self.Watersnood +  str(e))
                ET.phoneHome(str(e))
                traceback.print_exc(file=sys.stdout)
           
            
           
    #obsolete function in case of interrupt troubles on-site
    def buttonTesting(self):
        if GPIO.input(constants.BTN_SHUTDOWN) == GPIO.LOW:
            self.shutdown_h_now()
        
        if GPIO.input(constants.BTN_NAP) == GPIO.LOW:
            self.setNAPToZeroOrNot()
        else:
            self.Vlissingen.setToNormal()
            self.IJmuiden.setToNormal()
        
        if GPIO.input(constants.BTN_EMPTY) == GPIO.LOW:
            self.setNAPToEmptyOrNot()
        else:
            self.Vlissingen.setToNormal()
            self.IJmuiden.setToNormal()

    def shutdown_h_now(self):
        time.sleep(0.05)
        GPIO.cleanup()
        self.screen.clear()
        self.screen.writeInfoToScreen("Shutdown...")
        os.system("systemctl poweroff -i")
        time.sleep(3)
        self.screen.writeInfoToScreen("Bye...")
            
    def setNAPToZeroOrNot(self):
            self.IJmuiden.setLevelToZero()
            self.Vlissingen.setLevelToZero()
            
    def setNAPToEmptyOrNot(self):
            self.IJmuiden.setLevelToEmpty()
            self.Vlissingen.setLevelToEmpty()
    