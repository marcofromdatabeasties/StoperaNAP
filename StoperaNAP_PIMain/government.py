#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 16:19:43 2021

@author: ubuntu
"""

import urllib.request
import zipfile
from io import BytesIO
from datetime import timedelta
from datetime import datetime
import constants
import RPi.GPIO as GPIO
import traceback
import logging

class RWS:
    starttime=datetime.now() - timedelta(minutes=11) #bootstrap sentinel
    minutes_10 = timedelta(minutes=10)
    result = {}
    buttons_active = constants.BUTTONS_ACTIVE
    
    def getWaterLevel(self, measure_location):
        #test button on
        if self.buttons_active and (not GPIO.input(5)):
            return 0, True
        else:
            #Empty button on
            if (self.buttons_active and (not GPIO.input(6))):
                return constants.NAP_COLUMN_LEVEL, True
            else:
                if ((self.starttime + self.minutes_10 < datetime.now()) or (not measure_location in self.result)):
            
                    try:
                        mask = bytearray(b'     ')
                        if len(measure_location) <= 5 and len(measure_location) >= 2 and measure_location.isupper():
                            byteCode = bytearray(measure_location.strip().encode('utf-8'))
                            
                            for idx, b in enumerate(bytearray(byteCode)):
                                mask[idx] = b
                        else:
                            return 1, False
                        
                        if mask in self.validCodes():
                            
                            with urllib.request.urlopen(constants.RWS_URL) as response:
                               zipFromURL = response.read()
                               zippie = zipfile.ZipFile(BytesIO(zipFromURL))
                               dat = zippie.read('update.dat')
                               adm = zippie.read('update.adm')
                               
                               data = dat.splitlines()
                            
                               for idx, line in enumerate(adm.splitlines()):
                                   
                                   if line[15:18] == b'H10' and line[4:9] == mask:
                                      #print (data[idx][:len(data[idx])-1])
                                      measures = str(data[idx][:len(data[idx])-1],'utf-8').split(",")
                                      #print (measures, flush=True)
                                      #level of NAP 
                                      value = min( float(measures[len(measures)-1].strip()) / 100.0, constants.NAP_COLUMN_MAX_LEVEL)
                                      
                                      self.result[measure_location] = value
                                      self.starttime = datetime.now()
                                      #print("NAP {location} = {value} ".format(location = measure_location, value=value))
                                      return value, True
                        else:
                            return 2, False
                        
                    except:
                        logging.error(traceback.format_exc())
                        return 3, False
                else:
                    return self.result[measure_location], True
                
    def validCodes(self): 
    	return [	b'AMRO ',
    	b'AMRB ',
    	b'ARNH ',
    	b'BAAL ',
    	b'BATH ',
    	b'BBDT ',
    	b'BELF ',
    	b'BELB ',
    	b'BDSL ',
    	b'BOM1 ',
    	b'BORJ ',
    	b'BORD ',
    	b'BORS ',
    	b'BRES ',
    	b'BG2  ',
    	b'BG8  ',
    	b'BRO2 ',
    	b'BRO6 ',
    	b'BUND ',
    	b'CADZ ',
    	b'CULB ',
    	b'DLFZ ',
    	b'DENH ',
    	b'OEBI ',
    	b'OEBU ',
    	b'DEVE ',
    	b'DOES ',
    	b'DORD ',
    	b'DRIO ',
    	b'DRIB ',
    	b'ECHT ',
    	b'EDAM ',
    	b'EMSH ',
    	b'EIJS ',
    	b'ELBB ',
    	b'ELSL ',
    	b'EPL1 ',
    	b'GENN ',
    	b'GOID ',
    	b'GOUD ',
    	b'GRAV ',
    	b'GRAB ',
    	b'HAGO ',
    	b'HAGB ',
    	b'HANS ',
    	b'HA10 ',
    	b'HARL ',
    	b'HEEO ',
    	b'HEEB ',
    	b'HEES ',
    	b'HELL ',
    	b'HOEK ',
    	b'HOLB ',
    	b'HOLW ',
    	b'HOUN ',
    	b'HOUZ ',
    	b'HUIB ',
    	b'IJMH ',
    	b'IJMO ',
    	b'IJMW ',
    	b'IJSS ',
    	b'K131 ',
    	b'KADL ',
    	b'KALO ',
    	b'KAMP ',
    	b'KAMH ',
    	b'KATV ',
    	b'KATS ',
    	b'KEIZ ',
    	b'KETH ',
    	b'KOBI ',
    	b'KOBU ',
    	b'KRAZ ',
    	b'KRSL ',
    	b'KRIY ',
    	b'KRIL ',
    	b'LAUW ',
    	b'LEMM ',
    	b'LEG1 ',
    	b'LIEF ',
    	b'LINN ',
    	b'LITB ',
    	b'LITO ',
    	b'LOBI ',
    	b'MAAR ',
    	b'MAAS ',
    	b'MRG  ',
    	b'MEGE ',
    	b'MOER ',
    	b'SPUI ',
    	b'MOND ',
    	b'MOOK ',
    	b'NEER ',
    	b'NESS ',
    	b'NWST ',
    	b'NWGN ',
    	b'NIJO ',
    	b'NIJW ',
    	b'NIJM ',
    	b'OLST ',
    	b'OS11 ',
    	b'OS14 ',
    	b'OS4  ',
    	b'OUDE ',
    	b'OVHA ',
    	b'PANN ',
    	b'PROS ',
    	b'Q11  ',
    	b'RAKN ',
    	b'RAKZ ',
    	b'RAMS ',
    	b'ROER ',
    	b'ROGN ',
    	b'ROGZ ',
    	b'RPBI ',
    	b'RPBU ',
    	b'ROTT ',
    	b'SAMO ',
    	b'SAMB ',
    	b'SVDN ',
    	b'SCHWB',
    	b'SCHE ',
    	b'SCHI ',
    	b'SCHH ',
    	b'SINT ',
    	b'KGTB ',
    	b'SPIJ ',
    	b'SPBI ',
    	b'STEL ',
    	b'STEV ',
    	b'SPY1 ',
    	b'SURI ',
    	b'TERN ',
    	b'TERS ',
    	b'TEXE ',
    	b'TIEW ',
    	b'TIEK ',
    	b'VECO ',
    	b'VM3  ',
    	b'VM4  ',
    	b'VM5  ',
    	b'VENL ',
    	b'VLAA ',
    	b'VR   ',
    	b'VLIE ',
    	b'VLIS ',
    	b'VK   ',
    	b'VOSM ',
    	b'VURE ',
    	b'WALS ',
    	b'WEES ',
    	b'WELL ',
    	b'WERK ',
    	b'WTER ',
    	b'WKAP ',
    	b'WIER ',
    	b'WIJK ',
    	b'YE   ',
    	b'ZALT ',
    	b'ZUTP ',
    	b'ZWBU ',
    ]
    
if __name__ == "__main__":
    

    rws = RWS()
    print (rws.getWaterLevel(constants.COLUMN_1_LOCATION))
    print (rws.getWaterLevel(constants.COLUMN_2_LOCATION))
    print (rws.getWaterLevel(constants.COLUMN_1_LOCATION))