#!/usr/bin/python

from datetime import datetime
from datetime import timedelta
import subprocess
import time
import atexit

from wrappers import GPhoto
from wrappers import Identify
from wrappers import NetworkInfo

from config_persist import Persist
from ui import TimelapseUi

MIN_INTER_SHOT_DELAY_SECONDS = timedelta(seconds=30)
MIN_BRIGHTNESS = 20000
MAX_BRIGHTNESS = 30000
IMAGE_DIRECTORY = "DCIM/"

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
    camera = GPhoto(subprocess)
    idy = Identify(subprocess)
    netinfo = NetworkInfo(subprocess)

    model = camera.get_model()
    print "%s" %model

    persist = Persist()
    ui = TimelapseUi()

    current_config = 10
    initVal = 14
    current_config = persist.readLastConfig(initVal)
    shot = 1 
    prev_acquired = None
    last_acquired = None
    last_started = None

    network_status = netinfo.network_status()
    #current_config = ui.main(CONFIGS, current_config, network_status)

    try:
        while True:
            last_started = datetime.now()
            config = CONFIGS[current_config]
            print "Shot: %d Shutter: %s ISO: %d" % (shot, config[1], config[3])
            #ui.backlight_on()
            #ui.show_status(shot, CONFIGS, current_config)
            camera.set_shutter_speed(secs=config[1])
            camera.set_iso(iso=str(config[3]))
            print "Camera settings done"
            #ui.backlight_off()
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
               persist.writeLastConfig(current_config)
            elif brightness > MAX_BRIGHTNESS and current_config > 0:
               current_config = current_config - 1
               persist.writeLastConfig(current_config)
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

    #https://docs.python.org/2/library/atexit.html
    atexit.register(exit_handler)

if __name__ == "__main__":
    main()
