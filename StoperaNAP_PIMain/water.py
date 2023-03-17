#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:35:01 2021

@author: ubuntu

This file holds the water columns type

"""

import states
from pressure import PressureSensor
import constants
from datetime import timedelta, datetime
from time import time

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
        
    def getWaterLevel(self):
        if (self.zero):
            return 0.0
        if (self.empty):
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
        level_column = constants.NAP_COLUMN_LEVEL + self.pressureSensor.getColumnLevel(self.channel)
            
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
        self.screen.writeToScreen(self.measure_location, self.state.getName(), level_column 
                                  , level_desired, self.screenRow)
        
     
                
class WaterColumn1953 (WaterColumn):
    
    start_time = datetime.now()
    
    def getWaterLevel(self):
        if (self.zero):
            return 0
        if (self.empty):
            return constants.NAP_COLUMN_LEVEL
        if self.start_time + timedelta(minutes=(constants.HALF_CYCLE_TIME_1953 * 2)) < datetime.now():
                self.start_time = datetime.now()
        if self.start_time + timedelta(minutes=constants.HALF_CYCLE_TIME_1953) < datetime.now():
            return 0.0
        else:
            return constants.LEVEL_1953
            
            
        
            
        
    
            
         
    
    
                