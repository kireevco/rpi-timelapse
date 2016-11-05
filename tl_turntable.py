#!/usr/bin/python

from datetime import datetime
from datetime import timedelta
import time
import atexit
import os
import sys
import shutil
import RPi.GPIO as GPIO

from wrappers import GPhoto
from wrappers import Identify
from wrappers import NetworkInfo

from config_persist import Persist

import subprocess
import logging
import signal

__version__ = "1.0"
MIN_INTER_SHOT_DELAY_SECONDS = timedelta(seconds=600)
MIN_BRIGHTNESS = 12000
MAX_BRIGHTNESS = 17000
IMAGE_DIRECTORY = "/var/lib/timelapse/img/"
TMP_DIRECTORY = "/tmp/"
SETTINGS_FILE = "/var/lib/timelapse/settings.cfg"
INIT_CONFIG = 20
INIT_SHOT = 0
INIT_FLASH = False
SLEEP_TIME = 1
FLASH_THRESHOLD = 19
LOG_FILENAME = '/var/log/timelapse.log'

outPin = 21
GPIO.setmode(GPIO.BCM)
GPIO.setup(outPin, GPIO.OUT)

class App():

    def __init__(self):
        self.shot = 0

        self.displaySet = False

    def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        GPIO.cleanup()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    def startup(self):
        self.shoot()

    def run(self):
        self.startup()

    def handleLight(self, enabled):
        if (enabled):
            GPIO.output(outPin,True)
        else:
            GPIO.output(outPin,False)

    def turnLightOn(self):
        self.handleLight(True)

    def turnLightOff(self):
        self.handleLight(False)


    def main(self):
        self.testConfigs()

    def shoot(self):
        self.turnLightOn();

        def exit_handler():
            print 'Shooting aborted!'

        # https://docs.python.org/2/library/atexit.html
        atexit.register(exit_handler)

if __name__ == "__main__":
    app = App().run()
