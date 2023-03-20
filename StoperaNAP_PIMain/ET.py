#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  3 16:03:46 2023

@author: marco
"""

import urllib.request
import constants
import time
import logging

import json

def phoneHome(what):
    try:
        req = urllib.request.Request(constants.NAPLogger)
        req.add_header('Content-Type', 'application/json')
        
        jsondata = json.dumps({"log": what })
        jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
        req.add_header('Content-Length', len(jsondataasbytes))
    
        with urllib.request.urlopen(req, jsondataasbytes) as f:
            f.read()
    
    finally:
        time.sleep(.05)
        logging.debug(what)
 