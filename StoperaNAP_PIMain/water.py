#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:35:01 2021

@author: ubuntu

This file holds the water columns type

"""

import time
import states
import government
from pressure import Pressure
from datetime import timedelta
from datetime import datetime
import constants


class WaterColumn:
    state = states.NoWhere()
    measure_location = ""
    pin_valve = -1
    pin_pump = -1
    pressureSensor = Pressure()
    rws = government.RWS()
    
    counter = 0;
    
    previous_level = 0
    previous_desired = 0
    
    
    def __init__(self, location, channel, pin_valve, pin_pump ):
        self.channel = channel
        self.measure_location = location
        self.pin_pump = pin_pump
        self.pin_valve=pin_valve
            
    def runWorlds(self, screen):
        while True:
            #NAP start  + NAP level equals column height 
            level_column = constants.NAP_COLUMN_LEVEL + self.pressureSensor.getWaterLevel(self.channel)                
            level_desired, error = self.rws.getWaterLevel(self.measure_location)
            if (not error):
                self.previous_desired = level_desired
            else:
                level_desired = self.previous_desired
                
            self.state = self.state.execute(self.measure_location, level_column, level_desired,  self.pin_valve, self.pin_pump, screen)
            
            #check if an hardware error is occuring
            if (self.previous_level == self.level_column and level_desired > level_column):
                self.counter += 1
                if (self.counter > constants.TEN_S_EQUAL_ERROR_COUNT): #1 minute no change in water level, something is wrong -> Error
                    self.state = states.Error()
                    
            else:
                self.counter = 0
                self.previous_level = self.level_column
            
            screen.writeToScreen(self.channel, self.measure_location, self.state.getName(), self.level_column , self.level_desired)
            time.sleep(constants.COLUMN_WAIT) 
            
            
class WaterColumn1953(WaterColumn):
    
    starttime=datetime.now()
    quater = timedelta(minutes=constants.CYCLE_TIME_1953)
    highorlow = False
    
    def __init__(self, location, channel, pin_valve, pin_pump ):
        super().__init__(location, channel, pin_valve, pin_pump)
        
    def runWorlds(self, screen):
        while True:
            level_column = self.pressureSensor.getWaterLevel(self.channel)
            if (self.highorlow):
                level_desired = 4.55 #https://www.rijkswaterstaat.nl/water/waterbeheer/bescherming-tegen-het-water/watersnoodramp-1953
            else:
                level_desired = 0
            if (self.starttime + self.quater < datetime.now()):
                self.highorlow = not self.highorlow
                self.starttime = datetime.now()
                
            self.state = self.state.execute(self.measure_location, level_column, level_desired,  self.pin_valve, self.pin_pump)
            screen.writeToScreen(self.channel, self.measure_location, self.state.getName(), self.level_column , self.level_desired)
            time.sleep(constants.COLUMN_WAIT)               
                
                
        
         
    
    
                