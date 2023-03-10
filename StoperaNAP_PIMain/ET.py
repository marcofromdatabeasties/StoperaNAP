#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  3 16:03:46 2023

@author: marco
"""

import urllib.request
import constants

import json

def phoneHome(what):
    try:
        req = urllib.request.Request(constants.NAPLogger)
        req.add_header('Content-Type', 'application/json')
        
        jsondata = json.dumps({"log": what })
        jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
        req.add_header('Content-Length', len(jsondataasbytes))
    
        response = urllib.request.urlopen(req, jsondataasbytes)
    
    finally:
        dummy = 1; 
    
if __name__ == "__main__":
    phoneHome("test")
    
    try:
        app()
        
    except Exception as e:
       phoneHome(str(e))