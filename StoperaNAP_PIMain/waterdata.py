#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  2 15:07:09 2023

@author: marco
"""

import urllib.request
from datetime import timedelta, datetime
import constants
import json
import logging
#from numpy.core.defchararray import startswith

class RWS:
    minutes_10 = timedelta(minutes=10)
    result = {}
    catalogus = {}
    catalogus_time = {}
    
    #Note checken of GPIO werkt.
    
    
    def getLastUpdate(self):
        return self.catalogus_time
    

    def getCatalogus(self):
        req = urllib.request.Request(constants.WaterData['RetrieveCatalogus'])
        req.add_header('Content-Type', 'application/json')
        
        jsondata = json.dumps(constants.WaterData['RetrieveCatalogusBody'])
        jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
        req.add_header('Content-Length', len(jsondataasbytes))
        
        try:

            with urllib.request.urlopen(req, jsondataasbytes) as response:
                body = response.read()
                if (response.status == 200):
                    result = json.loads(body.decode("utf-8"))
                    self.catalogus = result['LocatieLijst']
                    return True
                return False
        except Exception as e:
            logging.exception("%s", str(e))
            return False
    
    def getWaterLevel(self, measure_location):
        #when new data is expected retreive data       
        if (not measure_location in self.catalogus_time.keys()):
            #sentinel
            self.catalogus_time[measure_location] = datetime.now() - self.minutes_10
        
        if (datetime.now() > self.catalogus_time[measure_location]):
            
            loc = self.getLocation(measure_location);
            if loc != False:
                data = {"AquoPlusWaarnemingMetadataLijst" :[{"AquoMetadata":{"Compartiment": 
                            {"Code":"OW"},"Eenheid":{"Code":"cm"},
                            "Hoedanigheid":{"Code":"NAP"}}}],
                            "LocatieLijst":[loc]}
                
                req = urllib.request.Request(constants.WaterData['RetrieveObservation'])
                req.add_header('Content-Type', 'application/json')
                
                jsondata = json.dumps(data)
                jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
                req.add_header('Content-Length', len(jsondataasbytes))
        
                with urllib.request.urlopen(req, jsondataasbytes) as response:
                    body = response.read()
                    if (response.status == 200):
                        doc = json.loads(body.decode("utf-8"))
                        observations = doc['WaarnemingenLijst'][0]
                        measurements = observations['MetingenLijst'][0]
                        
                        measurement = measurements['Meetwaarde']
                        value = measurement['Waarde_Numeriek'] / 100 # to meters
                        self.result[measure_location] = value 
                        self.catalogus_time[measure_location] = datetime.now() + self.minutes_10
                        logging.info("OK, retrieved new waterlevel for %s" % measure_location)
                        return value

        return self.result[measure_location]
        
    
    def getLocation(self, code):
        if self.getCatalogus():            
            for location in self.catalogus:
                if location["Code"] == code:
                    return location
        return False
        
if __name__ == "__main__":
    
    #GPIO.setmode(GPIO.BCM)
    
    rws = RWS()
    #print (rws.getWaterLevel(constants.COLUMN_1_LOCATION))
    #print (rws.getWaterLevel(constants.COLUMN_2_LOCATION))
    #print (rws.getWaterLevel(constants.COLUMN_1_LOCATION))
    
    # print ( rws.isEmptying(24, 0))
    # print ( rws.isEmptying(22, 0))
    # print ( rws.isEmptying(22, 5))
    # print ( rws.isEmptying(22, 6))
    # print ( rws.isEmptying(8, 0))
    rws.getCatalogus()
    print(rws.getCatalogus())
    #for location in rws.catalogus:
    #            if location["Code"].startswith("IJM" ):
    #               print( location)
    #print(rws.catalogus)
    
    print(rws.getWaterLevel("IJMH"))
    
    logging.debug('test123')
    # print(rws.getWaterLevel("IJMH"))
    # print(rws.getWaterLevel("IJMH"))
    # print(rws.getWaterLevel("RPBU"))
    # print(rws.getWaterLevel("RPBU"))
    # print(rws.getWaterLevel("RPBU"))
    #


