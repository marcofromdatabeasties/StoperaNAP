#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 19:24:54 2022

@author: marco
"""

import RPi.GPIO as GPIO
import constants
import time
import signal
import sys

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":

    GPIO.setmode(GPIO.BCM) 
    GPIO.setwarnings(True)
    GPIO.setup(constants.PUMP_IJMUIDEN, GPIO.OUT)
    GPIO.setup(constants.PUMP_VLISSINGEN, GPIO.OUT)
    GPIO.setup(constants.VL_IJMUIDEN, GPIO.OUT)
    GPIO.setup(constants.VL_VLISSINGEN, GPIO.OUT)
    
    
    while (True):
                
         GPIO.output(constants.VL_IJMUIDEN, GPIO.HIGH)
         GPIO.output(constants.VL_VLISSINGEN, GPIO.HIGH)
         
         GPIO.output(constants.PUMP_IJMUIDEN, GPIO.HIGH)
         GPIO.output(constants.PUMP_VLISSINGEN, GPIO.HIGH)
         
         time.sleep(1)
                 
         GPIO.output(constants.VL_IJMUIDEN, GPIO.LOW)
         GPIO.output(constants.VL_VLISSINGEN, GPIO.LOW)
         
         GPIO.output(constants.PUMP_IJMUIDEN, GPIO.LOW)
         GPIO.output(constants.PUMP_VLISSINGEN, GPIO.LOW)

         time.sleep(1)
                 
         
