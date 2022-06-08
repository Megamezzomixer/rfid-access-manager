import configparser
import os
from mfrc522 import SimpleMFRC522

class RFIDManager:
    def __init__(self):
        global _reader
        _reader = SimpleMFRC522()
        config = configparser.ConfigParser()
        if os.path.exists("config.ini"):
            config.read("config.ini")
            global _DEBUG
            _DEBUG = config["General"].getboolean("Debug")
    
    def readRFID(self):
        print("[RFIDManagement] Waiting for a tag in reader proximity...")
        try:
            _uid, _ident = _reader.read()
            
            _uidStripped = str.replace(str(_uid), " ", "") # Removes unwanted empty chars
            _identStripped = str.replace(str(_ident), " ", "") # Removes unwanted empty chars
            
            if(_DEBUG):
                print("[DEBUG/RFIDManagement] Captured UID: '" + _uidStripped + "' Identifier: '" +  _identStripped + "'")
            return _uidStripped, _identStripped
        
        except KeyboardInterrupt:
            print("[RFIDManagement] Reading process aborted.")
            return None
    def writeRFID(self, ident:str):
        if(_DEBUG):
            print("[DEBUG/RFIDManagement] Writing ident '" + ident + "' to tag")
        print("[RFIDManagement] Writing random identification key to tag...")
        _reader.write(ident)