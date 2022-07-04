#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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