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

"""
import socket
import logging
import RPi.GPIO as GPIO
import constants

class State:
    def handleState(self, level_column, level_desired):
        
        level_desired_min = level_desired - abs(level_desired * constants.ACCURACY_OF_COLUMN)
        level_desired_max = level_desired + abs(level_desired * constants.ACCURACY_OF_COLUMN)
        
        level_column_min = level_column - abs(level_column * constants.ACCURACY_OF_COLUMN)
        level_column_max = level_column + abs(level_column * constants.ACCURACY_OF_COLUMN)

        
        if (level_column_min <= level_desired <= level_column_max ):
            return Good()
        else:
            if (level_column_min < level_desired_min):
                return Low()
            else:
                if (level_column_max > level_desired_max):
                    return High()

class NoWhere(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        IPaddress = self.get_ip()
        if IPaddress == "127.0.0.1":
            logging.info("No internet ")
            screen.writeInfoToScreen("No IP connection")
            return self
        else:
            logging.info("Connected, with the IP address: %s", IPaddress )
            screen.writeInfoToScreen("IP: {IPaddress}".format( IPaddress = IPaddress))
            return  Start()
    def getName(self):
        return "N"
    
    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

class Good(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("%s = Level good ", location)
        GPIO.output(pin_valve, GPIO.LOW)
        GPIO.output(pin_pump, GPIO.LOW)
        return self.handleState(level_column, level_desired) 
   
    def getName(self):
        return "G"
    

class High(State):
    def execute(self, location,level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("%s = Too high ", location)
        GPIO.output(pin_valve, GPIO.HIGH)
        GPIO.output(pin_pump, GPIO.LOW)
        return self.handleState(level_column, level_desired)
    
    def getName(self):
        return "H"
        
class Low(State):
    def execute(self, location, level_column, level_desired, pin_valve, pin_pump, screen):
        logging.info("%s = Too low", location)
        GPIO.output(pin_valve, GPIO.LOW)
        GPIO.output(pin_pump, GPIO.HIGH)
        return self.handleState(level_column, level_desired)

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
        GPIO.output(pin_valve, GPIO.LOW)
        GPIO.output(pin_pump, GPIO.LOW)
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