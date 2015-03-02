#!/usr/bin/python
    
from datetime import datetime
from datetime import timedelta
import time
import subprocess
import time
import atexit
import os
import sys
import shutil
import textwrap

from wrappers import GPhoto
from wrappers import Identify
from wrappers import NetworkInfo

from config_persist import Persist

import subprocess
import logging

from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from lcdScroll import Scroller

__version__ = "1.0"
MIN_INTER_SHOT_DELAY_SECONDS = timedelta(seconds=30)
MIN_BRIGHTNESS = 20000
MAX_BRIGHTNESS = 30000
IMAGE_DIRECTORY = "DCIM/"
SETTINGS_FILE = "settings.cfg"
INIT_CONFIG = 10
INIT_SHOT = 0
SLEEP_TIME = 1
LCD_CHAR_LINE_SIZE = 17
LOG_FILENAME = 'timelapse.log'

# Canon camera shutter settings
CONFIGS = [(48, "1/1600", 2, 100),
    (46, "1/1000", 2, 100),
    (45, "1/800", 2, 100),
    (43, "1/500", 2, 100),
    (41, "1/320", 2, 100),
    (40, "1/250", 2, 100),
    (29, "1/200", 2, 100),
    (38, "1/160", 2, 100),
    (36, "1/100", 2, 100),
    (35, "1/80", 2, 100),
    (34, "1/60", 2, 100),
    (33, "1/50", 2, 100),
    (32, "1/40", 2, 100),
    (31, "1/30", 2, 100),
    (29, "1/20", 2, 100),
    (28, "1/15", 2, 100),
    (27, "1/13", 2, 100),
    (26, "1/10", 2, 100),
    (24, "1/6", 2, 100),
    (23, "1/5", 2, 100),
    (22, "1/4", 2, 100),
    (21, "0.3", 2, 100),
    (19, "0.5", 2, 100),
    (18, "0.6", 2, 100),
    (17, "0.8", 2, 100),
    (16, "1", 2, 100),
    (14, "1.6", 2, 100),
    (12, "2.5", 2, 100),
    (11, "3.2", 2, 100),
    ( 9, "5", 2, 100),
    ( 7, "8", 2, 100),
    ( 6, "10", 2, 100),
    ( 5, "13", 2, 100),
    ( 4, "15", 2, 100),
    ( 3, "20", 2, 100),
    ( 1, "30", 2, 100),
    ( 1, "30", 3, 200),
    ( 1, "30", 4, 400),
    ( 1, "30", 4, 800),
    ( 1, "30", 5, 1600)]



class App(Adafruit_CharLCDPlate):

    def __init__(self):
        self.LCDAttached = self.checkPanel()
        # Initialize the LCD using the pins
        # see https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/usage
        if (self.LCDAttached == True):
          Adafruit_CharLCDPlate.__init__(self)
        self.camera = GPhoto(subprocess)
        self.idy = Identify(subprocess)
        self.netinfo = NetworkInfo(subprocess)
        self.shot = 0
        
        self.displaySet = False

    def startup(self):
        if (self.LCDAttached == True):
          self.clear()
          self.backlight(self.WHITE)
        logging.basicConfig(filename='%s/timelapse.log' % os.path.dirname(os.path.realpath(__file__)), level=logging.INFO, format='%(asctime)s %(message)s')
        logging.info('Started %s' % __file__)
        logging.info("Timelapse Version %s"%__version__)
        if (self.LCDAttached == True):
            self.message("Timelapse\nVersion %s"%__version__)
            logging.info('LCD attached')
        else:
            logging.info('LCD NOT attached')

        time.sleep(SLEEP_TIME)

        self.getNetwork()
        self.getModel()

        self.shoot()

    def run(self):
        self.startup()

    def showConfig(self, current):
        config = CONFIGS[current]
        self.message("Timelapse\nT:%s ISO:%d" % (config[1], int(config[3])))

    def showStatus(self, shot, current):
        config = CONFIGS[current]
        self.clear()
        self.message("Shot %d\nT:%s ISO:%d" % (shot, config[1], int(config[3])))

    def printToLcd(self, message):
        self.message('\n'.join(textwrap.wrap(message, LCD_CHAR_LINE_SIZE)))

    def getNetwork(self):
        network_status = self.netinfo.network_status()
        if (self.LCDAttached == True):
            self.backlight(self.TEAL)
            self.clear()
            self.message(network_status)
            time.sleep(SLEEP_TIME)
        logging.info(network_status)

    def stop(self, mode):
        self.clear()
        logging.info("Goodbye!")
        self.message("Goodbye!")
        # flashy ending!
        for i in range(3):
            for col in (self.YELLOW, self.GREEN, self.TEAL, self.BLUE, self.VIOLET, self.WHITE, self.RED):
                self.backlight(col)
                time.sleep(.05)
        time.sleep(SLEEP_TIME)
        self.backlight(self.OFF)
        self.noDisplay()
        logging.info("Display off")
        if mode == "exit":
            logging.info("End")
            sys.exit()
        if mode == "shutdown":
            logging.info("Shutown")
            os.system("sudo shutdown -h now")

    def cleanUp(self, e):
        logging.error(str(e))
        self.backlight(self.RED) 
        self.clear()
        lines=[str(e)]
        displayScroll = Scroller(lines=lines)
        message = displayScroll.scroll()
        self.message(message)
        self.speed = .5
        while True:
            # sel = 1, r = 2, d = 4, u = 8, l = 16
            if self.buttonPressed(self.UP): 
                self.stop('exit')
            self.clear()
            scrolled = displayScroll.scroll()
            self.message(scrolled)
            time.sleep(self.speed)
        raise Exception(str(e))

    def chooseSetting(self, configs, current):
        ready = False
        while not ready:
            while True:
                if self.buttonPressed(self.UP):
                    print "UP"
                    current -= 1
                if current < 0:
                    current = 0
                    break
                if self.buttonPressed(self.DOWN):
                    print "DOWN"
                    current += 1
                if current >= len(configs):
                    current = len(configs) - 1
                    break
                if self.buttonPressed(self.SELECT):
                    print "SELECT"
                    ready = True
                    break
            config = configs[current]
            logging.info("Settings done")
            self.printToLcd("Timelapse\nT: %s ISO: %s" % (config[1], config[3]))
        return current

    def testConfigs():
        print "Testing Configs"
        camera = GPhoto(subprocess)

        for config in CONFIGS:
            print "Testing camera setting: Shutter: %s ISO %d" % (config[1], config[3])
            camera.set_shutter_speed(secs=config[1])
            camera.set_iso(iso=str(config[3]))
            time.sleep(SLEEP_TIME)
            lcd = Adafruit_CharLCDPlate()
            lcd.clear()
            lcd.backlight(lcd.TEAL)

    def main():
        test_configs()


    def checkPanel(self):

        LCDAttached = False
        # Check if the LCD panel is connected
        # sudo apt-get install i2c-tools
        p = subprocess.Popen('sudo i2cdetect -y 1', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            if line[0:6] == "20: 20":
                LCDAttached=True
            retval = p.wait()
        return LCDAttached

    def getModel(self):
        model = "undef" 
        try:
            model = self.camera.get_model()
        except Exception, e:
            if (self.LCDAttached == True):
                self.cleanUp(e)
            else:
                raise Exception(str(e))

        self.clear()
        self.message(model)
        logging.info(model)
        time.sleep(SLEEP_TIME)

    def shoot(self):
        persist = Persist()
        settings = persist.readLastConfig(INIT_CONFIG, INIT_SHOT, SETTINGS_FILE)
        current_config = settings["lastConfig"]
        self.shot = settings["lastShot"] + 1 

        if (self.LCDAttached == True):
            self.clear()

        if (os.path.exists(IMAGE_DIRECTORY) or self.shot != 1) :
            if (self.LCDAttached == True):
                self.printToLcd("Wanna continue shooting?")
                while True:
                    if self.buttonPressed(self.UP):
                        quest = "y"
                        break
                    elif self.buttonPressed(self.DOWN):
                        quest = "n"
                        break
            else:
                quest = raw_input("Wanna continue shooting? (y/n): ")

            if quest=="n":
                logging.info('NOT continue shooting')
                current_config = INIT_CONFIG
                self.shot = INIT_SHOT+1

                if (self.LCDAttached == True):
                    self.clear()
                    self.printToLcd("Starting new shooting")
                    logging.info('Starting new shooting')
                    time.sleep(SLEEP_TIME)         
                    self.clear()
                    self.printToLcd("Wanna delete all files?")
                    while True:
                        if self.buttonPressed(self.UP):
                            delete = "y"
                            break
                        elif self.buttonPressed(self.DOWN):
                            delete = "n"
                            break
                else:
                    logging.info('Starting new shooting!')
                    delete = raw_input("Delete settings and all images in folder %s ? (y/n): " % (IMAGE_DIRECTORY))

                if delete=="y":
                    if os.path.exists(IMAGE_DIRECTORY):
                        shutil.rmtree(IMAGE_DIRECTORY)
                    if os.path.exists(SETTINGS_FILE):
                        os.remove(SETTINGS_FILE)
                    if (LCDAttached == True):
                        self.printToLcd('Deleted successfully')
                        logging.info('Deleted successfully')
                    else:
                        logging.info('Deleted successfully')
                elif delete=="n":
                    logging.info("Saving in folder: %s " % (IMAGE_DIRECTORY))
                    if (self.LCDAttached == True):
                        self.clear()
                        self.printToLcd("Saving in folder: %s " % (IMAGE_DIRECTORY))
                        time.sleep(SLEEP_TIME)
                        self.clear()
                    else:
                        print "Saving in folder: %s " % (IMAGE_DIRECTORY)
                else:
                    raise Exception("Input failure, exiting!")
            elif quest=="y":
                if (self.LCDAttached == True):
                    self.clear()
                    self.printToLcd("Continue with shot %s" % (self.shot))
                    logging.info('Continue shooting with shot %s' % (self.shot))
                    time.sleep(SLEEP_TIME)
                    self.clear()
                else:
                    logging.info('Continue shooting with shot %s' % (self.shot))
                    print "Continue shooting with shot %s" % (self.shot)
            else:
                raise Exception("Input failure, exiting!")

        prev_acquired = None
        last_acquired = None
        last_started = None

        if (self.LCDAttached == True):
            config = CONFIGS[current_config]
            logging.info("Inital setting: T: %s ISO: %d" % (config[1], config[3]))
            self.message("Timelapse\nT:%s ISO:%d" % (config[1], config[3]))
            current_config = self.chooseSetting(CONFIGS, current_config)
        try:
            while True:
                last_started = datetime.now()
                config = CONFIGS[current_config]
                logging.info("Shot: %d T: %s ISO: %d" % (self.shot, config[1], config[3]))
                if (self.LCDAttached == True):
                    self.showStatus(self.shot, current_config)
                else:
                    print "Shot: %d T: %s ISO: %d" % (self.shot, config[1], config[3])
                try:
                    self.camera.set_shutter_speed(config[1])
                    self.camera.set_iso(iso=str(config[3]))
                except Exception, e:
                    if (self.LCDAttached == True):
                        self.cleanUp(e)
                try:
                    filename = self.camera.capture_image_and_download(shot=self.shot, image_directory=IMAGE_DIRECTORY)
                except Exception, e:
                    logging.error("Error on capture." + str(e))
                    print "Error on capture." + str(e)
                    print "Retrying..."
                    # Occasionally, capture can fail but retries will be successful.
                    continue
                prev_acquired = last_acquired
                brightness = float(self.idy.mean_brightness(IMAGE_DIRECTORY+filename))
                last_acquired = datetime.now()

                logging.info("Shot: %d File: %s Brightness: %s" % (self.shot, filename, brightness))

                if brightness < MIN_BRIGHTNESS and current_config < len(CONFIGS) - 1:
                    current_config = current_config + 1
                    persist.writeLastConfig(current_config, self.shot, brightness, SETTINGS_FILE)
                elif brightness > MAX_BRIGHTNESS and current_config > 0:
                    current_config = current_config - 1
                    persist.writeLastConfig(current_config, self.shot, brightness, SETTINGS_FILE)
                else:
                    if last_started and last_acquired and last_acquired - last_started < MIN_INTER_SHOT_DELAY_SECONDS:
                        logging.info("Sleeping for %s" % str(MIN_INTER_SHOT_DELAY_SECONDS - (last_acquired - last_started)))
                        print "Sleeping for %s" % str(MIN_INTER_SHOT_DELAY_SECONDS - (last_acquired - last_started))

                        time.sleep((MIN_INTER_SHOT_DELAY_SECONDS - (last_acquired - last_started)).seconds)
                self.shot += 1
        except Exception,e:
            logging.error("Error: %s" %(str(e)))
            print "Error: %s" %(str(e))

        def exit_handler():
            if (self.LCDAttached == True):
                self.backlight(self.RED) 
                self.clear()
                self.message('Shooting aborted!')
            else:
                print 'Shooting aborted!'

        # https://docs.python.org/2/library/atexit.html
        atexit.register(exit_handler)

if __name__ == "__main__":
    app = App().run()
