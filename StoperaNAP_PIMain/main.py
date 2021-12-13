#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 13:18:45 2021

@author: ubuntu
"""
import logging

from NAPMonument import NAPMonument

def main():
    logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%H:%M:%S")
    logging.setLevel(logging.ERROR)
    
    monument = NAPMonument()
    monument.start()
    

if __name__ == "__main__":
    main()
