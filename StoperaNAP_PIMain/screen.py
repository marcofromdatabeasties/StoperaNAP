#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 23 21:45:15 2021

@author: ubuntu
"""

from RPLCD.i2c import CharLCD


class LCD:
    
    lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
              cols=20, rows=4, dotsize=8,
              charmap='A02',
              auto_linebreaks=True,
              backlight_enabled=True)
    
    def __init__(self):
        self.lcd.cursor_pos = (4, 0)
        self.lcd.write_string("  ©Stopera/NAP/RWS")

    def writeToScreen(self, channel, location, status, current_level , desired_level):
        text = "{location} {status} {current_level:0.2f}/{desired_level:0.2f}".format(location = location, status = status, 
                current_level=round(current_level, 2) , desired_level = round(desired_level, 2))
        self.lcd.cursor_pos = (channel, 0)
        self.lcd.write_string(text)