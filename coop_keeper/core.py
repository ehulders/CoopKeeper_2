from __future__ import annotations
from typing import MutableSequence
import pytz
import time
import datetime as dt
import logging
import asyncio
import os
import subprocess

#import RPi.GPIO as GPIO

from threading import Thread, Event
from astral import Astral

from abc import ABC, abstractmethod


APP_NAME = "CoopKeeper"


logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/tmp/{}.log'.format(APP_NAME))
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

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


class Door:
    
    _state = None
    _mode = None

    def __init__(self, state: State, mode: Mode) -> None:
        self.set_state(state)
        self.set_mode(mode)

    def set_state(self, state: State):
        self._state = state
        self._state.door = self
    
    def set_mode(self, mode: Mode):
        self._mode = mode
        self._mode.ck = self

    def present_state(self):
        #logger.info(f"CoopKeeper door is {type(self._state).__name__}")
        return type(self._state).__name__

    def present_mode(self):
        #logger.info(f"CoopKeeper mode is {type(self._mode).__name__}")
        return type(self._mode).__name__

    def push_open_button(self):
        self._state.push_open_button()

    def push_close_button(self):
        self._state.push_close_button()
    
    def hold_open_button(self):
        self._mode.hold_open_button()

    def hold_close_button(self):
        self._mode.hold_close_button()

    def push_both_buttons(self) -> None:
        logger.warning("Oops.. you should press one button at a time")

    def no_button_pushed(self) -> None:
        logger.info("Press any button. Open or close")

 
class State(ABC):
    @property
    def door(self) -> Door:
        return self._door

    @door.setter
    def door(self, door: Door) -> None:
        self._door = door

    @abstractmethod
    def push_open_button(self) -> None:
        pass

    @abstractmethod
    def push_close_button(self) -> None:
        pass


class Closed(State):
    def push_close_button(self):
        msg = f"CoopKeeper door is already {type(self.door._state).__name__}"
        logger.warning(msg)
        return msg

    def push_open_button(self):
        msg = "Door is opening."
        logger.info(msg)
        logger.info("Door is open.")
        self.door.set_state(Open())
        return msg


class Open(State):
    def push_close_button(self):
        msg = "Door is closing"
        logger.info(msg)
        logger.info("Door is closed.")
        self.door.set_state(Closed())
        return msg

    def push_open_button(self):
        msg = f"CoopKeeper door is already {type(self.door._state).__name__}"
        logger.warning(msg)
        return msg


class Mode(ABC):
    @property
    def door(self) -> Door:
        return self._door

    @door.setter
    def door(self, door: Door) -> None:
        self._door = door

    @abstractmethod
    def hold_open_button(self) -> None:
        pass

    @abstractmethod
    def hold_close_button(self) -> None:
        pass


class Auto(Mode):
    def hold_close_button(self):
        msg = "CoopKeeper switching to manual."
        logger.info(msg)
        self.ck.set_mode(Manual())
        return msg

    def hold_open_button(self):
        msg = "CoopKeeper switching to manual."
        logger.info(msg)
        self.ck.set_mode(Manual())
        return msg


class Manual(Mode):
    def hold_close_button(self):
        msg = "CoopKeeper switching to auto."
        logger.info(msg)
        self.ck.set_mode(Auto())
        return msg

    def hold_open_button(self):
        msg = "CoopKeeper switching to auto."
        logger.info(msg)
        self.ck.set_mode(Auto())
        return msg


class CoopKeeper:
    def __init__(self):
        #GPIOInit()
        self.door = Door(Closed(), Auto())
        #self.buttons = Buttons(self)
        #self.enviro_vars = EnviroVars(self)
        self.coop_time = CoopClock(self)


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

                if (self.current_time < self.open_time or self.current_time > self.close_time) and self.ck.door.present_state() != "Closed":
                    logger.info("Door should be closed based on time of day")
                    self.ck.door.push_close_button()
                    #Event().wait(5)

                elif self.current_time > self.open_time and self.current_time < self.close_time and self.ck.door.present_state() != "Open":
                    logger.info("Door should be open based on time of day")
                    self.ck.door.push_open_button()
                    #Event().wait(5)

            Event().wait(1)