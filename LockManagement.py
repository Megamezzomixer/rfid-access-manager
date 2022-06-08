import configparser
from enum import Enum
import os
from time import sleep
import time
from gpiozero import LED
from gpiozero import PWMLED
from datetime import datetime
class LockManager:
    
    def _loadConfiguration(self):
        config = configparser.ConfigParser()
        if os.path.exists("config.ini"):
            config.read("config.ini")
            global _DEBUG
            _DEBUG = config["General"].getboolean("Debug")
            global _OPEN_TIME
            _OPEN_TIME = config["General"].getint("Door-Open-Time")
            global _ACCESS_LOG
            _ACCESS_LOG = config["General"].getboolean("Access-Logging")
            global _ACCESS_LOG_PATH
            _ACCESS_LOG_PATH = config["General"].get("Access-Log-Path")


            global _LOCK
            _LOCK = LED(config["Lock-GPIO"].get("Lock"))
            global _BUZZER
            _BUZZER = PWMLED(config["Lock-GPIO"].get("Buzzer"))
            global _LED_RED
            _LED_RED = LED(config["Lock-GPIO"].get("LED-Red"))
            global _LED_GREEN
            _LED_GREEN = LED(config["Lock-GPIO"].get("LED-Green"))
            
    def cleanup(self):
        _BUZZER.close()
        _LED_GREEN.close()
        _LED_RED.close()
        _LOCK.close()
        if(_DEBUG):
            print("[DEBUG/LockManagement] GPIO Cleanup performed")

    def appendLog(self, message: str):
        if(_ACCESS_LOG):
            try:
                if(os.path.exists(_ACCESS_LOG_PATH)):
                    append_write = "a"
                else:
                    append_write = "w"
                logfile = open(_ACCESS_LOG_PATH, append_write)
                now = datetime.now()
                currentTime = now.strftime("%m.%d.%Y %H:%M:%S")
                logfile.write(currentTime + " " + message + "\n")
            except IOError as err:
                print("[LockManagement] Logging Error: " + str(err))
                self.buzz(BuzzStatus.ERROR)

    def buzz(self, status):
        match status:
            case BuzzStatus.ERROR:
                if(_DEBUG):
                    print("[DEBUG/LockManagement] Buzzing an Errorstatus")
                _BUZZER.frequency = 600
                _BUZZER.pulse(.1, 0, 4)
                sleep(1) # Needed, so that the Buzzer doesn't get cleaned up before being done buzzing
            case BuzzStatus.ACCESS_GRANTED:
                if(_DEBUG):
                    print("[DEBUG/LockManagement] Buzzing Access Granted")
                _BUZZER.frequency = 900
                _BUZZER.blink(.1, 0, 1)
                time.sleep(.1)
                _BUZZER.frequency = 1200
                _BUZZER.blink(.1, 0, 1)
                time.sleep(.1)
                _BUZZER.frequency = 1400
                _BUZZER.blink(.1, 0, 1)
                time.sleep(.1)
                _BUZZER.off()
                
            case BuzzStatus.ACCESS_DENIED:
                if(_DEBUG):
                    print("[DEBUG/LockManagement] Buzzing Access Denied")
                _BUZZER.frequency = 900
                _BUZZER.pulse(.1, 0, 1)
                time.sleep(.1)
                _BUZZER.frequency = 800
                _BUZZER.pulse(.1, 0, 1)
                time.sleep(.1)
                _BUZZER.off()
                
            case BuzzStatus.TEST:
                if(_DEBUG):
                    print("[DEBUG/LockManagement] Buzzing Test")
                _BUZZER.frequency = 1400
                _BUZZER.pulse(.1, 0, 1)
            case _:
                if(_DEBUG):
                    print("[DEBUG/LockManagement] Buzzing an Errorstatus")
                _BUZZER.frequency = 400
                _BUZZER.pulse(.1, 0, 4)
                sleep(1) # Needed, so that the Buzzer doesn't get cleaned up before being done buzzing
                
    def unlock(self):
        self._lockDisengage()
        self.ledGreen(_OPEN_TIME)
        self.buzz(BuzzStatus.ACCESS_GRANTED)
        time.sleep(_OPEN_TIME)
        self._lockEngage()
        
    def ledRed(self, time=2):
        if(_DEBUG):
            print("[DEBUG/LockManagement] Red LED triggered")
        _LED_RED.blink(time,0,1)
    def ledGreen(self, time=2):
        if(_DEBUG):
            print("[DEBUG/LockManagement] Green LED triggered")
        _LED_GREEN.blink(time,0,1)
        
    def _lockEngage(self):
        if(_DEBUG):
            print("[DEBUG/LockManagement] Lock Engaged")
        _LOCK.on()
        
    def _lockDisengage(self):
        if(_DEBUG):
            print("[DEBUG/LockManagement] Lock Disengaged")
        _LOCK.off()
        
    def __init__(self):
        self._loadConfiguration()
        self._lockEngage()
    
class BuzzStatus(Enum):
    ACCESS_GRANTED = 0
    ERROR = 1
    ACCESS_DENIED = 2
    TEST = 3