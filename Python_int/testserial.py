# -*- coding: utf-8 -*-
"""
Created on Wed May  5 13:59:14 2021

@author: Henry
"""

import serial




ser = serial.Serial (port="COM4", baudrate=9600,
                      bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                      stopbits=serial.STOPBITS_ONE,
                      timeout=None,
                      xonxoff=False,
                      rtscts=False, 
                      write_timeout=None, 
                      dsrdtr=False,
                      inter_byte_timeout=None)



ser.write("A")


ser.close()