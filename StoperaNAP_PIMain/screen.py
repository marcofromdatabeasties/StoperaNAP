#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 23 21:45:15 2021

@author: ubuntu
"""

from RPLCD.i2c import CharLCD
import time


class LCD:
    
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
              cols=20, rows=4, dotsize=8,
              charmap='A00',
              auto_linebreaks=False,
              backlight_enabled=True)
    
    def __init__(self):
        self.lcd.cursor_pos = (3, 0)
        self.lcd.write_string("V3.1 St. NAP/RWS/Stopera"[:18])
        self.ms = time.time()
        self.lastRow = -1
        self.times = 0
        self.lcd.cursor_mode = 'hide'
        self.lcd.noAutoscroll()

    def writeToScreen(self, location, status, current_level , desired_level, screenRow):
        
        #timing to reduce screen update problems.
        if (self.ms + 1 < time.time()) and self.lastRow != screenRow:
            kolom_ind = location[0:2] 
        
            text = ("{kolom_ind} {status} {current_level:0.2f}/{desired_level:0.2f}" + (' ' * 10)).format(
                    kolom_ind = kolom_ind, status = status, 
                    current_level=current_level , desired_level = desired_level)
            text = text[:18]
            #print(text)
            self.lcd.cursor_pos = (screenRow, 0)
            self.lcd.write_string(text)
            self.ms = time.time()
            self.lastRow = screenRow
            self.times += 1
        
        if self.times % 33 == 0:
            self.clear()
    
        
    def writeInfoToScreen(self, message):
        self.lcd.cursor_pos = (3, 0)
        self.lcd.write_string((("{message}" + (' ' * 19)).format(message = message[:18])[:18]))
        
    def clear(self):
        self.lcd.clear()
        self.lcd.cursor_pos = (3, 0)
        self.lcd.write_string("NAP/RWS/Stopera"[:18])
        
        
        