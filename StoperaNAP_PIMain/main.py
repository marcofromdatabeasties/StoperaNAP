#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:18:45 2021

@author: ubuntu
"""
import logging
from logging.handlers import RotatingFileHandler
from NAPMonument import NAPMonument

def main():
    
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

    logFile = '/tmp/nap.log'
    
    my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=512*1024, 
                                     backupCount=1, encoding=None, delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.INFO)
    
    app_log = logging.getLogger('root')
    app_log.setLevel(logging.INFO)
    
    app_log.addHandler(my_handler)
    
    logging.info("Starting")
    #start monument
    try: 
        monument = NAPMonument()
        monument.start()
    except Exception as e:
       logging.exception(str(e)) 
    

if __name__ == "__main__":
    
    main()
    
    