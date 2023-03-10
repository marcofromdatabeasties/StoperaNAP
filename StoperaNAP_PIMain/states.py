#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 14:28:32 2021

@author: ubuntu
"""

"""
LOW = 0; // world 1: water in kolom te laag tov NAP/ water in column to low
HIGH = 1; // world 2: water in kolom te hoog tov NAP/water in column to high
GOOD = 2; // world 3: water in kolom goed tov NAP/water in column ok
ERROR = 3; // world 4: water in kolom veranderd niet / meting onjuist/ error world: water is not moving or measurement is off.
START = 4; //world 5: starting (INet)
NOWHERE = 5;//boot

Remember LOW = on

"""
import logging
import RPi.GPIO as GPIO
import constants
import time 

class State:
    
    def handleState(self, level_column, level_desired):
        
        level_desired_min = level_desired - abs(constants.NAP_COLUMN_HEIGHT * constants.ACCURACY_OF_COLUMN)
        level_desired_max = level_desired + abs(constants.NAP_COLUMN_HEIGHT * constants.ACCURACY_OF_COLUMN)
        
        level_column_min = level_column - abs(constants.NAP_COLUMN_HEIGHT * constants.ACCURACY_OF_COLUMN)
        level_column_max = level_column + abs(constants.NAP_COLUMN_HEIGHT * constants.ACCURACY_OF_COLUMN)

        new_state = Start()
    
        
        if (level_column_min <= level_desired <= level_column_max ):
            new_state = Good()
        else:
            if (level_column_min < level_desired_min):
                new_state = Low()
            else:
                if (level_column_max > level_desired_max):
                    new_state = High()
                    
        return new_state
        

class NoWhere(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        screen.writeInfoToScreen("Startup")
        GPIO.output(pin_valve, GPIO.HIGH)
        GPIO.output(pin_pump, GPIO.HIGH)
        
        new_state = Pauze()
        new_state.start_time = time.time()
        new_state.delta_time = 2
        return new_state

    def getName(self):
        return "N"

class Good(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("%s = Level good ", location)
        GPIO.output(pin_valve, GPIO.HIGH)
        GPIO.output(pin_pump, GPIO.HIGH)
        
        new_state = Off()
        new_state.start_time = time.time()
        new_state.delta_time = 90 
    
        return new_state
        #return self.handleState(level_column, level_desired) 
   
    def getName(self):
        return "G"
    
class Off(State):
    start_time = -1
    delta_time = 0
    
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("%s = off", location)
        GPIO.output(pin_valve, GPIO.HIGH)
        GPIO.output(pin_pump, GPIO.HIGH)
        
        if self.start_time + self.delta_time < time.time():
            return self.handleState(level_column, level_desired)
        
        return self
   
    def getName(self):
        return "R"
    
class Pauze(State):
    start_time = -1
    delta_time = 0 
    
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("%s = pauze", location)
        
        new_state = self
        if self.start_time + self.delta_time < time.time():
            new_state = Off()
            new_state.start_time = time.time()
            new_state.delta_time = 10  
        
        return new_state
       
    def getName(self):
        return "P"        
    

class High(State):
    def execute(self, location,level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("%s = Too high ", location)
        GPIO.output(pin_valve, GPIO.LOW)
        GPIO.output(pin_pump, GPIO.HIGH)
       
        
        new_state = Pauze()
        new_state.start_time = time.time()
        new_state.delta_time = max(0.5, min(20, abs((level_column*100) - (level_desired*100))/5))
        
        return new_state
    
    def getName(self):
        return "H"
        
class Low(State):
    start_time = -1
    delta_time = 0 
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("%s = Too low", location)
        GPIO.output(pin_valve, GPIO.HIGH)
        GPIO.output(pin_pump, GPIO.LOW)
        
        new_state = Pauze()
        new_state.start_time = time.time()
        new_state.delta_time = max(1, min(50, abs((level_column*100) - (level_desired*100))/2))
        
        return new_state

    def getName(self):
        return "L"


class Start(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("Starting %s", location)
        return self.handleState(level_column, level_desired) 
    
    def getName(self):
        return "S"
                
class Error(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("%s = Error", location)
        GPIO.output(pin_valve, GPIO.HIGH)
        GPIO.output(pin_pump, GPIO.HIGH)
        return self
   
    def getName(self):
        return "E"        
    
if __name__ == "__main__":
    state = State()
    print (state.handleState(-1.01, -1.00))
    print (state.handleState(3.00, 1.05))
    print (state.handleState(1.00, 3.00))
    
    nowhere = NoWhere()
    print (nowhere.get_ip())