#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:35:01 2021

@author: ubuntu

This file holds the water columns type

"""

import states
from pressure import Pressure
import constants

class WaterColumn:
    state = states.NoWhere()
    measure_location = ""
    pin_valve = -1
    pin_pump = -1
    pressureSensor = Pressure()
    
    counter = 0;
    
    previous_level = 0
    previous_desired = 0
    
    
    def __init__(self, location, channel, pin_valve, pin_pump, pressureSensor, screen, rws ):
        self.channel = channel
        self.measure_location = location
        self.pin_pump = pin_pump
        self.pin_valve = pin_valve
        self.zero = False
        self.empty = False
        self.pressureSensor = pressureSensor
        self.screen = screen
        self.rws = rws
        
    def getWaterLevel(self):
        if (self.zero):
            return 0, True
        if (self.empty):
            return constants.NAP_COLUMN_LEVEL, True
        return self.rws.getWaterLevel(self.measure_location)
    
    def setLevelToZero(self):
        #only set when empty is false
        self.zero = not self.empty
    
    def setLevelToEmpty(self):
        #only set when zero  is false
        self.empty = not self.zero
        
    def setToNormal(self):
        self.zero = False
        self.empty = False
            
    def runWorlds(self):
        #NAP start  + NAP level equals column height 
        level_column = constants.NAP_COLUMN_LEVEL + self.pressureSensor.getColumnLevel(self.channel)
            
        level_desired, ok = self.getWaterLevel() 
        
        if (ok):
            self.previous_desired = level_desired
        else:
            #print("error")
            
            level_desired = self.previous_desired
        
        if (ok):
            self.state = self.state.execute(self.measure_location, level_column, level_desired,  self.pin_valve, self.pin_pump, self.screen)
        else:
            self.state = states.Error()
        
        #check if an hardware error is occuring
        if (self.previous_level == level_column and level_desired > level_column):
            self.counter += 1
            if (self.counter > constants.TEN_S_EQUAL_ERROR_COUNT): #no change in water level after x iterations, something is wrong -> Error
                self.state = states.Error()
                
        else:
            self.counter = 0
            self.previous_level = level_column
        #print ("Level Desired Column {0:2.2f}".format(level_desired))
        self.screen.writeToScreen(self.measure_location, self.state.getName(), level_column , level_desired)
                
                
        
         
    
    
                