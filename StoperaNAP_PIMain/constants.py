#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import adafruit_ads1x15.ads1015 as ADS

"""
Created on Sun Oct 24 20:47:15 2021

@author: ubuntu
"""

NAP_COLUMN_LEVEL = -2.15 #neters to NAP
NAP_COLUMN_HEIGHT = 6.15 #max column height
NAP_COLUMN_MAX_LEVEL = {
    "IJMH": 3.5, #max_level
    "RPBU": 4.0  #max_level
}
TEN_S_EQUAL_ERROR_COUNT = 50 #times level stays the same
COLUMN_WAIT = 2 
CYCLE_TIME_1953=15
RWS_URL="https://www.rijkswaterstaat.nl/rws/opendata/meetdata/meetdata.zip"
COLUMN_1_LOCATION="IJMH"
COLUMN_2_LOCATION="RPBU"
BUTTONS_ACTIVE=True #use the buttons or not
ACCURACY_OF_COLUMN=0.05 #% of accuracy
NO_WEEKEND = True #run on weekend (False) or not

#screen
ROW = {
    "IJMH": 0, 
    "RPBU": 1  
}

#pinouts
PUMP_VLISSINGEN = 16
PUMP_IJMUIDEN = 20
PUMP_53 = 21
VL_53 = 25
VL_IJMUIDEN = 7
VL_VLISSINGEN = 12

#Buttons
BTN_SHUTDOWN = 13
BTN_NAP = 19
BTN_EMPTY = 26

PR_VLISSINGEN = ADS.P1
PR_IJMUIDEN = ADS.P2
PR_53 = ADS.P3s