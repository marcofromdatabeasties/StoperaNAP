#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:35:01 2021

@author: Marco

This file holds the water columns type

"""

import states
from pressure import PressureSensor
import constants
from datetime import timedelta, datetime
import logging

class WaterColumn:
    state = states.NoWhere()
    measure_location = ""
    pin_valve = -1
    pin_pump = -1
    pressureSensor = PressureSensor()
    
    counter = 0;
    
    previous_level = 0
    previous_desired = 0
    
    
    def __init__(self, location, channel, pin_valve, pin_pump, pressureSensor, screen, rws, screenRow ):
        self.channel = channel
        self.measure_location = location
        self.pin_pump = pin_pump
        self.pin_valve = pin_valve
        self.zero = False
        self.empty = False
        self.pressureSensor = pressureSensor
        self.screen = screen
        self.rws = rws
        self.screenRow = screenRow
        
    def isEmptying(self, hour, day):
         #monday is 0
         return ( not(5 <= hour <= 20)) or (day in {5, 6} and constants.NO_WEEKEND)
    
    def getWaterLevel(self):
        if (self.zero):
            return 0.0
        if (self.empty):
            return constants.NAP_COLUMN_LEVEL
        currenttime = datetime.now().time()
        day = datetime.today().weekday()
        hour = currenttime.hour
        if self.isEmptying(hour, day):
            return constants.NAP_COLUMN_LEVEL
        return self.rws.getWaterLevel(self.measure_location)
    
    def setLevelToZero(self):
        #only set when empty is false
        self.zero = True
    
    def setLevelToEmpty(self):
        #only set when zero  is false
        self.empty = True
        
    def setToNormal(self):
        self.zero = False
        self.empty = False
            
    def runWorlds(self):
        #NAP start  + NAP level equals column height
        raw_level, ok = self.pressureSensor.getColumnLevel(self.channel)
        if (ok):
            level_column = constants.NAP_COLUMN_LEVEL + raw_level
                
            level_desired = self.getWaterLevel() 
            
            self.state = self.state.execute(self.measure_location, level_column, level_desired,  self.pin_valve, self.pin_pump, self.screen)
                    
            #check if an hardware error is occuring
            if (self.previous_level == level_column and level_desired > level_column):
                self.counter += 1
                if (self.counter > constants.TEN_S_EQUAL_ERROR_COUNT): #no change in water level after x iterations, something is wrong -> Error
                    self.state = states.Error()
                    
            else:
                self.counter = 0
                self.previous_level = level_column
            #print ("Level Desired Column {0:2.2f}".format(level_desired))
            try:
                    
                self.screen.writeToScreen(self.measure_location, self.state.getName(), level_column 
                                      , level_desired, self.screenRow)
            except Exception as e:
                #writing to the screen is of less importance because nobody is watching most  of the time.
                #and because error 121 is a know bug of smb: 
                #    https://stackoverflow.com/questions/45324851/smbus-on-the-rpi-gives-ioerror-errno-121-remote-i-o-error
                #it will resolve over time by itself.
                logging.exception("%s", self.measure_location + str(e))
                    
     
                
class WaterColumn1953 (WaterColumn):
    
    start_time = datetime.now()
    
    def getWaterLevel(self):
        if (self.zero):
            return 0
        if (self.empty):
            return constants.NAP_COLUMN_LEVEL
        currenttime = datetime.now().time()
        day = datetime.today().weekday()
        hour = currenttime.hour
        if self.isEmptying(hour, day):
            return constants.NAP_COLUMN_LEVEL
        if self.start_time + timedelta(minutes=(constants.HALF_CYCLE_TIME_1953 * 2)) < datetime.now():
                self.start_time = datetime.now()
        if self.start_time + timedelta(minutes=constants.HALF_CYCLE_TIME_1953) < datetime.now():
            return 0.0
        else:
            return constants.LEVEL_1953
            
            
        
            
        
    
            
         
    
    
                