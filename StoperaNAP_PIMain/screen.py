#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 23 21:45:15 2021

@author: ubuntu
"""

from RPLCD.i2c import CharLCD
import time
import logging

class LCD:
    ms = time.time()
    lastRow = -1
    times = 0
    
    def __init__(self):
        self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
              cols=20, rows=4, dotsize=8,
              charmap='A00',
              auto_linebreaks=False,
              backlight_enabled=True)
        self.lcd.cursor_mode = 'hide'

    def writeToScreen(self, location, status, current_level , desired_level, screenRow):
        #timing to reduce screen update problems.
        if (self.ms + 1 < time.time()) and self.lastRow != screenRow:
            kolom_ind = location[0:4] 
        
            text = ("{kolom_ind} {status} {current_level:0.2f}/{desired_level:0.2f}" + (' ' * 5)).format(
                    kolom_ind = kolom_ind, status = status, 
                    current_level=current_level , desired_level = desired_level)
            text = text[:18]
            #print(text)
            self.lcd.cursor_pos = (screenRow, 0)
            time.sleep(0.10)
            self.lcd.write_string(text)
            time.sleep(0.10)
            self.ms = time.time()
            self.lastRow = screenRow
            self.times += 1
        
        if self.times % 33 == 0:
            self.lcd.cursor_mode = 'hide'
            self.clear()
            
    def writeManualToScreen(self, row, text):
        self.lcd.cursor_pos = (row, 0)
        time.sleep(0.10)
        self.lcd.write_string((("{text}" + (' ' * 19)).format(text = text[:18])[:18]))
        time.sleep(0.10)
    
        
    def writeInfoToScreen(self, message):
        self.lcd.cursor_pos = (3, 0)
        time.sleep(0.10)
        self.lcd.write_string((("{message}" + (' ' * 19)).format(message = message[:18])[:18]))
        time.sleep(0.10)
        
    def clear(self):
        try:
            self.lcd.clear()
            time.sleep(0.05)
        except Exception as e:
            logging.exception("Screen cleared: " + str(e))
        
        
        