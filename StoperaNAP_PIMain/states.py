#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 14:28:32 2021

@author: ubuntu
"""

"""
W1_LOW = 0; // world 1: water in kolom te laag tov NAP/ water in column to low
const static uint8_t W2_HIGH = 1; // world 2: water in kolom te hoog tov NAP/water in column to high
const static uint8_t W3_GOOD = 2; // world 3: water in kolom goed tov NAP/water in column ok
const static uint8_t W4_ERROR = 3; // world 4: water in kolom veranderd niet / meting onjuist/ error world: water is not moving or measurement is off.
const static uint8_t START = 4; //world 5: starting (INet)
const static uint8_t NOWHERE = 5;//boot

"""
import socket
import logging
import RPi.GPIO as GPIO

class State:
    def handleState(level_column, level_desired):
        level_desired_min = level_desired * 0.95
        level_desired_max = level_desired * 1.05
        if (level_column > level_desired_min and level_column < level_desired_max):
            return Good()
        else:
            if (level_column < level_desired_min):
                return Low()
            else:
                if (level_column > level_desired_max):
                    return High()

class NoWhere(State):
    def execute(self):
        IPaddress=socket.gethostbyname(socket.gethostname())
        if IPaddress=="127.0.0.1":
            logging.info("No internet ")
            return self
        else:
            logging.info("Connected, with the IP address: %s", IPaddress )
            return  Start()     

class Good(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump):
        logging.info("%s = Level good ", location)
        GPIO.output(pin_valve, GPIO.LOW)
        GPIO.output(pin_pump, GPIO.LOW)
        return self.handleState(level_column, level_desired)    
    

class High(State):
    def execute(self, location,level_column, level_desired, pin_valve, pin_pump):
        logging.info("%s = Too high ", location)
        GPIO.output(pin_valve, GPIO.HIGH)
        GPIO.output(pin_pump, GPIO.LOW)
        return self.handleState(level_column, level_desired)
        
class Low(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump):
        logging.info("%s = Too low", location)
        GPIO.output(pin_valve, GPIO.LOW)
        GPIO.output(pin_pump, GPIO.HIGH)
        return self.handleState(level_column, level_desired)

class Start(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump):
        logging.info("Starting %s", location)
        return self.handleState(level_column, level_desired) 
                
        