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
import traceback
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
        
        
        GPIO.setup(constants.BTN_SELECT, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(constants.BTN_DO, GPIO.IN, GPIO.PUD_UP) 
        GPIO.setup(constants.BTN_MANUAL, GPIO.IN, GPIO.PUD_UP) 
    
    def __init__(self):
        self.buttonsUp()
        self.screen = LCD()
        time.sleep(1)
        self.screen.clear()
        if not (self.ping(constants.WaterData["NU"]) 
                        and self.ping(constants.WaterData["GOOGLE"])
                        and self.ping(constants.WaterData["AWS"])
                        and self.ping(constants.WaterData["NOS"])):
            for i in range(0,6):
                self.screen.writeInfoToScreen("Wcht %s min gn dta" % str(5-i))
                time.sleep(60) #sleep 5 minutes
                
        self.pressureSensor = PressureSensor()
        self.rws = RWS()
        self.starttime = datetime.now() - timedelta(days=1)
        self.phonetime = datetime.now()
        self.target = 0
        self.refresh = 1
        self.running = False
        ET.phoneHome("Wake up")
       
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


        #main loop
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
                self.starttime = datetime.now() + timedelta(hours=8)
                logging.error("No ip", str(e))
                ET.phoneHome("ip error: %s" % str(e))
                traceback.print_stack()
                if not (self.ping(constants.WaterData["NU"]) 
                        and self.ping(constants.WaterData["GOOGLE"])
                        and self.ping(constants.WaterData["AWS"])
                        and self.ping(constants.WaterData["NOS"])):
                    #nobody home, link down? let's reboot
                    os.system("sudo reboot")
                    
            if self.phonetime + timedelta(hours=1) < datetime.now():
                ET.phoneHome("working....")
                self.phonetime = datetime.now() + timedelta(hours=1)
            #normal operation
            if GPIO.input(constants.BTN_MANUAL) == GPIO.HIGH: 
                if not self.running:
                    self.doGPIO( GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)
                    self.screen.clear()
                    self.running = True
                #adjust levels
                try:
                    self.IJmuiden.runWorlds()
                    time.sleep(constants.COLUMN_WAIT)
                except Exception as e:
                        logging.exception("%s", self.IJmuiden.measure_location + str(e))
                        ET.phoneHome("%s" % self.IJmuiden.measure_location + str(e))
                        traceback.print_stack()
                
                try:    
                    self.Watersnood.runWorlds()
                    time.sleep(constants.COLUMN_WAIT)
                except Exception as e:
                        logging.exception("%s", self.Watersnood.measure_location + str(e))
                        ET.phoneHome("%s" % self.Watersnood.measure_location + str(e))
                        traceback.print_stack()
                
                try:
                    self.Vlissingen.runWorlds()
                    time.sleep(constants.COLUMN_WAIT)
                except Exception as e:
                        logging.exception("%s", self.Vlissingen.measure_location + str(e))
                        ET.phoneHome("%s" % self.Vlissingen.measure_location + str(e))
                        traceback.print_stack()
            else:
                time.sleep(constants.COLUMN_WAIT)
                #select manuele selectie modus
                if (self.running):
                    self.running = False
                    self.doGPIO( GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)
                    self.screen.clear()
                if GPIO.input(constants.BTN_SELECT) == GPIO.LOW and GPIO.input(constants.BTN_DO) == GPIO.HIGH:
                    self.doGPIO( GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)
                    #clear screen
                    try:
                        self.refresh = (self.refresh + 1) % 33
                        if not self.refresh:
                            self.screen.clear()
                            
                        self.target = (self.target + 1) % 6
                        if self.target == 0:
                            self.screen.writeInfoToScreen("Handm 1953 Vullen")
                        else: 
                            if self.target == 1:
                                self.screen.writeInfoToScreen("Handm VLIS Vullen")
                            else:
                                if self.target == 2:
                                    self.screen.writeInfoToScreen("Handm IJMN Vullen")
                                else: 
                                    if self.target == 3:
                                        self.screen.writeInfoToScreen("Handm 1953 Legen")
                                    else: 
                                        if self.target == 4:
                                            self.screen.writeInfoToScreen("Handm VLIS Legen")
                                        else: 
                                            if self.target == 5:
                                                self.screen.writeInfoToScreen("Handm IJMN Legen")
                    except Exception as e:
                        logging.exception("%s", str(e))
                #select doe vullen of legen
                if  GPIO.input(constants.BTN_DO) == GPIO.LOW and GPIO.input(constants.BTN_SELECT) == GPIO.HIGH:
                    try:
                        self.refresh = (self.refresh + 1) % 33
                        if not self.refresh:
                            self.screen.clear()
                    except Exception as e:
                         logging.exception("%s", str(e))
                         
                    if self.target == 0:
                        #1953 V
                       self.doGPIO( GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)
                       level, volt, ok = self.pressureSensor.getColumnLevelRaw(constants.PR_53)
                       self.writeManualToScreen(2, "1953 {level:0.2f}cm/{volt:0.2f}v".format( 
                           level= level, volt = volt))
                    else: 
                        if self.target == 1:
                            #Vlissingen V
                            self.doGPIO( GPIO.HIGH, GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)
                            level, volt, ok = self.pressureSensor.getColumnLevelRaw(constants.PR_VLISSINGEN)
                            self.writeManualToScreen(1, "VLIS {level:0.2f}cm/{volt:0.2f}v".format( 
                                level= level, volt = volt))
                        else:
                            if self.target == 2:
                                #Ijmuiden V
                                self.doGPIO( GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)
                                level, volt, ok = self.pressureSensor.getColumnLevelRaw(constants.PR_IJMUIDEN)
                                self.writeManualToScreen(0, "IJMN {level:0.2f}cm/{volt:0.2f}v".format( 
                                    level= level, volt = volt))
                            else: 
                                if self.target == 3:
                                    #1953 L
                                    self.doGPIO( GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.HIGH)
                                    level, volt, ok = self.pressureSensor.getColumnLevelRaw(constants.PR_53)
                                    self.writeManualToScreen(2, "1953 {level:0.2f}cm/{volt:0.2f}v".format( 
                                        level= level, volt = volt))
                                else: 
                                    if self.target == 4:
                                        #Vlissingen L
                                        self.doGPIO( GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.LOW)
                                        level, volt, ok = self.pressureSensor.getColumnLevelRaw(constants.PR_VLISSINGEN)
                                        self.writeManualToScreen(1, "VLIS {level:0.2f}cm/{volt:0.2f}v".format( 
                                            level= level, volt = volt))
                                    else: 
                                        if self.target == 5:
                                            #Ijmuiden L
                                            self.doGPIO( GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.LOW, GPIO.HIGH)
                                            level, volt, ok = self.pressureSensor.getColumnLevelRaw(constants.PR_IJMUIDEN)
                                            self.writeManualToScreen(0, "IJMN{level:0.2f}cm/{volt:0.2f}v".format( 
                                                level= level, volt = volt))
                                            
    def writeManualToScreen(self, row, text):
        try:
            self.screen.writeManualToScreen(row, text)
        except Exception as e:
             logging.exception("%s", str(e))
    
    def doGPIO(self, pump_53, pump_ijm, pump_vl, vl_53, vl_ijm, vl_vl):
        GPIO.output(constants.VL_IJMUIDEN, vl_ijm)
        GPIO.output(constants.VL_VLISSINGEN, vl_vl)
        GPIO.output(constants.VL_53, vl_53)
        
        GPIO.output(constants.PUMP_IJMUIDEN, pump_ijm)
        GPIO.output(constants.PUMP_VLISSINGEN, pump_vl)
        GPIO.output(constants.PUMP_53, pump_53)
    
    def ping(self, host):
        response = os.system("ping -c 1 " + host)
        
        #and then check the response...
        return  response == 0
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.doGPIO( GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)
