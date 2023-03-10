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
import sys, traceback
from datetime import timedelta, datetime
import urllib.request
import json

class NAPMonument:
    
    def buttonsUp(self):
    
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
    
    def __init__(self):
        self.buttonsUp()
        self.screen = LCD()
        time.sleep(1)
        self.screen.clear()
        self.screen.writeInfoToScreen("Hello! wait 5 min")
        for i in range(0,6):
            time.sleep(60*i) #sleep 5 minutes
            self.screen.writeInfoToScreen("Hello! wait %s min" % str(5-i))
        self.pressureSensor = PressureSensor()
        self.rws = RWS()
        ET.phoneHome("Wake up")
        self.starttime = datetime.now() - timedelta(days=1)
       
    def start(self):
        
        self.screen.writeInfoToScreen("Go")
        self.IJmuiden = WaterColumn(constants.COLUMN_1_LOCATION, constants.PR_IJMUIDEN
                                    , constants.VL_IJMUIDEN, constants.PUMP_IJMUIDEN
                                    , self.pressureSensor, self.screen, self.rws, 0) 
        
        self.Vlissingen = WaterColumn(constants.COLUMN_2_LOCATION, constants.PR_VLISSINGEN,
                                      constants.VL_VLISSINGEN,constants.PUMP_VLISSINGEN
                                      , self.pressureSensor, self.screen, self.rws, 1)
        
        self.Watersnood = WaterColumn1953(constants.COLUMN_3_LOCATION, constants.PR_53,
                                      constants.VL_53, constants.PUMP_53
                                      , self.pressureSensor, self.screen, self.rws, 2)


        
        while True:
            try:
                if self.starttime + timedelta(days=1) < datetime.now():
                    self.starttime = datetime.now()
                    req = urllib.request.Request(constants.IP_API)
                    ip = ""
                    with  urllib.request.urlopen(req) as response:
                        body = response.read()
                        if (response.status == 200):
                            result = json.loads(body.decode("utf-8"))
                            ip = result['ip']
                            time.sleep(1)
                        else:
                            self.starttime = datetime.now() + timedelta(hours=1)
                            
                    ET.phoneHome("remote ip: %s" % ip)
                    
            except Exception as e:
                starttime = datetime.now() + timedelta(hours=1)
                logging.error("No ip", str(e))
                ET.phoneHome("ip error: %s" % str(e))
                traceback.print_stack()    
            
            try:
                #self.buttonsUp()
                self.buttonTesting()
                self.IJmuiden.runWorlds()
                time.sleep(constants.COLUMN_WAIT)
            except Exception as e:
                    logging.error("%s", self.IJmuiden.measure_location + str(e))
                    ET.phoneHome("%s" % self.IJmuiden.measure_location + str(e))
                    traceback.print_stack()
            
            try:    
                self.Watersnood.runWorlds()
                time.sleep(constants.COLUMN_WAIT)
            except Exception as e:
                    logging.error("%s", self.Watersnood + str(e))
                    ET.phoneHome("%s" % self.Watersnood.measure_location + str(e))
                    traceback.print_stack()
            
            try:
                self.Vlissingen.runWorlds()
                time.sleep(constants.COLUMN_WAIT)
            except Exception as e:
                    logging.error("%s", self.Vlissingen.measure_location + str(e))
                    ET.phoneHome("%s" % self.Vlissingen.measure_location + str(e))
                    traceback.print_stack()
            
            
           
    #obsolete function in case of interrupt troubles on-site
    def buttonTesting(self):
        # GPIO.setmode(GPIO.BCM) 
        # GPIO.setwarnings(False)
        # GPIO.setup(constants.BTN_SHUTDOWN, GPIO.IN, GPIO.PUD_UP)
        # GPIO.setup(constants.BTN_EMPTY, GPIO.IN, GPIO.PUD_UP) 
        # GPIO.setup(constants.BTN_NAP, GPIO.IN, GPIO.PUD_UP)
        
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
    