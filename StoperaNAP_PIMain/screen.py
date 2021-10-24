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

    def writeToScreen(self, channel, location, status, current_level , desired_level):
        text = "{location} {status} {current_level}/{desired_level}".format(location = location, status = status, 
                current_level=current_level , desired_level = desired_level)
        self.lcd.cursor_pos = (channel, 0)
        self.lcd.write_string(text)