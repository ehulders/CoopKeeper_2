from __future__ import annotations
from typing import MutableSequence
import pytz
import time
import datetime as dt
import asyncio
import os
import subprocess

#import RPi.GPIO as GPIO

from threading import Thread, Event
from astral import Astral

from .door import Door, Idle, Auto, Neutral
from .logger import logger


"""
class GPIOInit:
    PIN_LED = 5
    PIN_BUTTON_UP = 4
    PIN_BUTTON_DOWN = 22
    PIN_SENSOR_TOP = 13
    PIN_SENSOR_BOTTOM = 16
    PIN_MOTOR_ENABLE = 25
    PIN_MOTOR_A = 24
    PIN_MOTOR_B = 23

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIOInit.PIN_MOTOR_ENABLE, GPIO.OUT)
        GPIO.setup(GPIOInit.PIN_MOTOR_A, GPIO.OUT)
        GPIO.setup(GPIOInit.PIN_MOTOR_B, GPIO.OUT)
        GPIO.setup(GPIOInit.PIN_LED, GPIO.OUT)
        GPIO.setup(GPIOInit.PIN_SENSOR_BOTTOM, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(GPIOInit.PIN_SENSOR_TOP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(GPIOInit.PIN_BUTTON_UP, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(GPIOInit.PIN_BUTTON_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
"""

class Location:
    
    TIMEZONE_CITY = 'Seattle'
    AFTER_SUNSET_DELAY = 10
    AFTER_SUNRISE_DELAY = 0


class CoopKeeper:
    
    def __init__(self):
        #GPIOInit()
        self.door = Door(Idle(), Auto(), Neutral())
        #self.buttons = Buttons(self)
        self.triggers = Triggers(self)
        self.coop_time = CoopClock(self)
        self.debug = Debug(self)
        

class Debug(Thread):
    
    def __init__(self, ck):
        Thread.__init__(self)
        self.ck = ck
        self.status = {
            "state": self.ck.door.present_state(), 
            "mode":  self.ck.door.present_mode(), 
            "position":  self.ck.door.present_position()
            }
        self.setDaemon(True)
        self.start()
    
    def run(self):
        while True:
            new_status = {
            "state": self.ck.door.present_state(), 
            "mode":  self.ck.door.present_mode(), 
            "position":  self.ck.door.present_position()
            }            
            if new_status != self.status:
                logger.info(new_status)
                self.status = new_status
            Event().wait(1)
    
    
class Triggers(Thread):

    def __init__(self, ck):
        Thread.__init__(self)
        self.ck = ck
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            if self.ck.door.present_state() == "Opening":
                self.ck.door.set_position(Neutral())
                Event().wait(5)
                self.ck.door.open_trigger()
                self.ck.door.set_state(Idle())
                
            if self.ck.door.present_state() == "Closing":
                self.ck.door.set_position(Neutral())
                Event().wait(5)
                self.ck.door.closed_trigger()
                self.ck.door.set_state(Idle())
                
            Event().wait(1)
            

class CoopClock(Thread):
    a = Astral()
    city = a[Location.TIMEZONE_CITY]

    def __init__(self, ck):
        Thread.__init__(self)
        self.current_time = None
        self.open_time = None
        self.close_time = None
        self.ck = ck
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            if self.ck.door.present_mode() == "Auto":
                sun = self.city.sun(date=dt.datetime.now(), local=True)
                self.open_time = sun["sunrise"] + dt.timedelta(minutes=Location.AFTER_SUNRISE_DELAY)
                self.close_time = sun["sunset"] + dt.timedelta(minutes=Location.AFTER_SUNSET_DELAY)
                self.current_time = dt.datetime.now(pytz.timezone(self.city.timezone))

                if (self.current_time < self.open_time or self.current_time > self.close_time) \
                    and self.ck.door.present_position() != "Closed" and self.ck.door.present_state() != "Closing":
                    logger.info("Door should be closed based on time of day")
                    self.ck.door.push_close_button()

                elif self.current_time > self.open_time and self.current_time < self.close_time \
                    and self.ck.door.present_position() != "Open" and self.ck.door.present_state() != "Opening":
                    logger.info("Door should be open based on time of day")
                    self.ck.door.push_open_button()
                
            Event().wait(1)