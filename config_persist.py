import os

class Persist():

    #http://stackoverflow.com/a/10352231/810944
    @staticmethod
    def touchopen(filename, *args, **kwargs):
        # Open the file in R/W and create if it doesn't exist. *Don't* pass O_TRUNC
        fd = os.open(filename, os.O_RDWR | os.O_CREAT)

        # Encapsulate the low-level file descriptor in a python file object
        return os.fdopen(fd, *args, **kwargs)

    @staticmethod
    def readLastConfig(initVal):
        filename = "settings.cfg"
        with Persist.touchopen(filename, "r+") as target:
            currentConfig = int(target.read() or int(initVal))

            # print "From file %s: %d" % (filename, currentConfig)
            return currentConfig

    @staticmethod
    def writeLastConfig(lastConfig):
        filename = "settings.cfg"
        with Persist.touchopen(filename, "r+") as target:
            # print "Writing to file %s: %s" % (filename, lastConfig)

            # Write the new value and truncate
            target.seek(0)
            target.write(str(lastConfig))
            target.truncate()
