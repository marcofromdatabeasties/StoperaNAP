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
        self.lcd.cursor_pos = (4, 0)
        self.lock.acquire(True, 10)
        self.lcd.write_string("V3.0 St. NAP/RWS")
        self.lock.release()

    def writeToScreen(self, channel, location, status, current_level , desired_level):
        self.lock.acquire(True, 10)
        text = "{location} {status} {current_level:0.2f}/{desired_level:0.2f}                       ".format(
                location = location, status = status, 
                current_level=round(current_level, 2) , desired_level = round(desired_level, 2))[:20]
        self.lcd.cursor_pos = (channel, 0)
        self.lcd.write_string(text)
        self.lock.release()
        
    def writeInfoToScreen(self, message):
        self.lock.acquire(True, 10)
        self.lcd.cursor_pos = (4, 0)
        self.lcd.write_string("{message}                    ".format(message = message[:20])[:20])
        self.lock.release()