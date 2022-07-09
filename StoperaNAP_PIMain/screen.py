#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 23 21:45:15 2021

@author: ubuntu
"""

from RPLCD.i2c import CharLCD
import threading


class LCD:
    
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
              cols=20, rows=4, dotsize=8,
              charmap='A02',
              auto_linebreaks=True,
              backlight_enabled=True)
    
    def __init__(self):
        self.lock = threading.Lock()
        self.lcd.cursor_pos = (3, 0)
        self.lock.acquire(True, 10)
        self.lcd.write_string("V3.0 St. NAP/RWS")
        self.lock.release()

    def writeToScreen(self, location, status, current_level , desired_level):
        self.lock.acquire(True, 10)
        
        text = ("{location} {status} {current_level:0.2f}/{desired_level:0.2f}" + (' ' * 20)).format(
                location = location, status = status, 
                current_level=current_level , desired_level = desired_level)[:20]
        #print(text)
        self.lcd.cursor_pos = (constants.ROW[self.location], 0)
        self.lcd.write_string(text)
        self.lock.release()
        
    def writeInfoToScreen(self, message):
        self.lock.acquire(True, 10)
        self.lcd.cursor_pos = (3, 0)
        self.lcd.write_string(("{message}" + (' ' * 20)).format(message = message[:20])[:20])
        self.lock.release()
        
    def clear(self):
        for i in [0,1,2]:
            self.lcd.cursor_pos = (i, 0)
            self.lcd.write_string(' ' * 20)
        
        
        