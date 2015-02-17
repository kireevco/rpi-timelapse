#!/usr/bin/python

from datetime import datetime
from datetime import timedelta
import subprocess
import time
import atexit
import os
import sys
import shutil

from wrappers import GPhoto
from wrappers import Identify
from wrappers import NetworkInfo

from config_persist import Persist
from ui import TimelapseUi

import subprocess

import Adafruit_CharLCD as LCD


def showConfig(lcd, current):
    config = CONFIGS[current]
    lcd.message("Timelapse\nT: %s ISO: %d" % (config[1], int(config[3])))

def showStatus(lcd, shot, current):
    config = CONFIGS[current]
    lcd.message("Shot %d\nT: %s ISO: %d" % (shot, config[1], int(config[3])))

def printToLcd(lcd, message):
    lcd.message(message)

MIN_INTER_SHOT_DELAY_SECONDS = timedelta(seconds=30)
MIN_BRIGHTNESS = 20000
MAX_BRIGHTNESS = 30000
IMAGE_DIRECTORY = "DCIM/"
SETTINGS_FILE = "settings.cfg"
INIT_CONFIG = 10
INIT_SHOT = 0
SLEEP_TIME = 3.0


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

def test_configs():
    camera = GPhoto(subprocess)

    for config in CONFIGS:
      print "Testing camera setting: Shutter: %s ISO %d" % (config[1], config[3])
      camera.set_shutter_speed(secs=config[1])
      camera.set_iso(iso=str(config[3]))
      time.sleep(1)

def main():
    #print "Testing Configs"
    #test_configs()
    print "Timelapse"
    LCDAttached=True #just to be sure 
    camera = GPhoto(subprocess)
    idy = Identify(subprocess)
    netinfo = NetworkInfo(subprocess)

    # Initialize the LCD using the pins 
    # see https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/usage
    lcd = LCD.Adafruit_CharLCDPlate()
    lcd.clear()
    lcd.set_color(1.0, 1.0, 1.0)
    model = camera.get_model()
    print "%s" %model

    # Check if the LCD panel is connected
    # sudo apt-get install i2c-tools
    p = subprocess.Popen('sudo i2cdetect -y 1', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
      if line[0:6] == "20: 20":
        LCDAttached=True
    retval = p.wait()

    persist = Persist()
    ui = TimelapseUi()

    if (LCDAttached == True):
      # color: white
      lcd.set_color(1.0, 1.0, 1.0)
      lcd.clear()
      printToLcd(lcd, model)
      time.sleep(SLEEP_TIME)

    settings = persist.readLastConfig(INIT_CONFIG, INIT_SHOT, SETTINGS_FILE)
    current_config = settings["lastConfig"]
    shot = settings["lastShot"] + 1 

    #lcd.clear()
    #showStatus(lcd,shot,current_config)
    #time.sleep(SLEEP_TIME)
 
    if (LCDAttached == True):
     lcd.clear()
     #showConfig(lcd, current_config)

    if (os.path.exists(IMAGE_DIRECTORY) or shot != 1) :
      quest = raw_input("Wanna continue shooting? (y/n): ")

      if quest=="n":
          current_config = INIT_CONFIG
          shot = INIT_SHOT+1
          print "Starting fresh shooting!"
          delete = raw_input("Delete settings and all images in folder %s ? (y/n): " % (IMAGE_DIRECTORY))
          if delete=="y":
              if os.path.exists(IMAGE_DIRECTORY):
                shutil.rmtree(IMAGE_DIRECTORY)
              if os.path.exists(SETTINGS_FILE):
                os.remove(SETTINGS_FILE)
              print "Deleted successfully"
          elif delete=="n":
              print "Saving in folder: %s " % (IMAGE_DIRECTORY)
          else:
              print "Input failure, exiting!"
              sys.exit()
      elif quest=="y":
          print "Continue shooting at shot %s" % (shot)
      else:
           print "Input failure, exiting!"
           sys.exit()

    prev_acquired = None
    last_acquired = None
    last_started = None

    if (LCDAttached == True):
      network_status = netinfo.network_status()
      print network_status
      current_config = ui.main(CONFIGS, current_config, network_status)

    try:
        while True:
            last_started = datetime.now()
            config = CONFIGS[current_config]
            print "Shot: %d Shutter: %s ISO: %d" % (shot, config[1], config[3])
            showStatus(lcd,shot,current_config)
            camera.set_shutter_speed(secs=config[1])
            camera.set_iso(iso=str(config[3]))
            print "Camera settings done"
            try:
              filename = camera.capture_image_and_download(shot=shot, image_directory=IMAGE_DIRECTORY)
            except Exception, e:
              print "Error on capture." + str(e)
              print "Retrying..."
              # Occasionally, capture can fail but retries will be successful.
              continue
            prev_acquired = last_acquired
            brightness = float(idy.mean_brightness(IMAGE_DIRECTORY+filename))
            last_acquired = datetime.now()

            print "-> %s %s" % (filename, brightness)

            if brightness < MIN_BRIGHTNESS and current_config < len(CONFIGS) - 1:
               current_config = current_config + 1
               persist.writeLastConfig(current_config, shot, brightness, SETTINGS_FILE)
            elif brightness > MAX_BRIGHTNESS and current_config > 0:
               current_config = current_config - 1
               persist.writeLastConfig(current_config, shot, brightness, SETTINGS_FILE)
            else:
                if last_started and last_acquired and last_acquired - last_started < MIN_INTER_SHOT_DELAY_SECONDS:
                    print "Sleeping for %s" % str(MIN_INTER_SHOT_DELAY_SECONDS - (last_acquired - last_started))

                    time.sleep((MIN_INTER_SHOT_DELAY_SECONDS - (last_acquired - last_started)).seconds)
            shot = shot + 1
    except Exception,e:
        #ui.show_error(str(e))
	print "Error: %s" %(str(e))

    def exit_handler():
        print 'Shooting aborted!'
        lcd.set_color(1.0, 0.0, 0.0)
        lcd.clear()
        lcd.message('Upps\nShooting aborted!')

    #https://docs.python.org/2/library/atexit.html
    atexit.register(exit_handler)

if __name__ == "__main__":
    main()
