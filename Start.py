#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
from re import T
import secrets
import signal
import os
import time
import datetime
import sys

from DBManangement import AccessStatus, DatabaseManager
from Identity import Identity
from LockManagement import BuzzStatus, LockManager
from RFIDManagement import RFIDManager

class Start:
    global _DBMANAGER
    _DBMANAGER = DatabaseManager()
    global _LOCKMANAGER
    _LOCKMANAGER = LockManager()
    global _RFIDMANAGER
    _RFIDMANAGER = RFIDManager()
    
    def loadConfiguration(self):
        config = configparser.ConfigParser()
        if os.path.exists("config.ini"):
            config.read("config.ini")
            global _DEBUG
            _DEBUG = config["General"].getboolean("Debug")


    def readMode(self):
        try:
            while(True):
                _uid, _ident = _RFIDMANAGER.readRFID() # Wait for RFID and get uid and chipside credential
                identity = Identity(None, _ident, _uid) # Wrap reader results into Identity instance
                validity, status = _DBMANAGER.checkIdentity(identity)
                if(validity):
                
                    # Access Granted, uid and ident correct
                    print("[Start] Access GRANTED for '" + identity.getName() + "'")
                    _LOCKMANAGER.appendLog("Access GRANTED for '" + identity.getName() + "'")
                    _LOCKMANAGER.unlock()
                else:
                    if(identity.getName() != None): # Log the name depending if we have it or not
                        print("[Start] Access DENIED for '" + identity.getName() + "'. Reason: " + status.name)
                        _LOCKMANAGER.appendLog("Access DENIED for '" + identity.getName() + "'. Reason: " + status.name)
                    else:
                        print("[Start] Access DENIED for '" + identity.getUID() + "'. Reason: " + status.name)
                        _LOCKMANAGER.appendLog("Access DENIED for '" + identity.getUID() + "'. Reason: " + status.name)
                        
                    _LOCKMANAGER.ledRed(3)
                    _LOCKMANAGER.buzz(BuzzStatus.ACCESS_DENIED)
                    time.sleep(3)
                
        except Exception as err:
            self.mainMenu()

    def exit(self, status=0):
        if(status != 0):
            _LOCKMANAGER.buzz(BuzzStatus.ERROR)
            
        _LOCKMANAGER.cleanup()
        _DBMANAGER.disconnect()
        print("[Start] Program Exit")
        exit(status)

    def mainMenu(self):
        
        print()
        print("---------------------------------------------")
        print("-        A D M I N I S T R A T I O N        -")
        print("-                 P A N E L                 -")
        print("---------------------------------------------")
        print("- 1: Enter Read Mode        2: Add Identity -")
        print("-                                           -")
        print("- 3: Remove Identity    4: Disable Identity -")
        print("-                                           -")
        print("- 5: Enable Identity    6: List Identities  -")
        print("-                                           -")
        print("- 7: Exit                                   -")
        print("---------------------------------------------")
        
        try:
            choice = input(">")
        except KeyboardInterrupt:
            self.exit()
        match choice:
            case "1":
                # Read Mode
                self.readMode()
            case "2":
                # Add Identity
                try:
                    os.system('clear')
                    _timedStart = None
                    _timedStop = None
                    
                    print("[Start] Please enter the name of the tag or its holder. It must be a unique one.")
                    print("[Start] NOTE: If you make a mistake, abort using CTRL+C and start over.")
                    _nameInput = input("Name: ")
                    print("[Start] Should the tag have timed access? (True/False)")
                    _timedAccessInput = input("Timed access? (True/False): ")
                    if(_timedAccessInput.lower() == "true"):
                        _timedAccess = True
                        
                        print("[Start] Specify the start hour of the timeframe (0-23)")
                        print("[Start] NOTE: The start hour cannot be higher or equal to the stop hour.")
                        _timeStartInput = input("Timeframe Starting hour (0-23): ")
                        try:
                            _timedStart = int(_timeStartInput)
                            if(_timedStart < 0 or _timedStart > 23):
                                raise TypeError
                            
                            print("[Start] Specify the stop hour of the timeframe (1-24)")
                            print("[Start] NOTE: The stop hour cannot be lower or equal to the start hour.")
                            _timeStopInput = input("Timeframe Stop hour (1-24): ")
                            _timedStop = int(_timeStopInput)
                            if(_timedStop < 1 or _timedStop > 24):
                                raise TypeError
                            
                        except TypeError:
                            print("[Start] Input not recognized, Exiting")
                            self.mainMenu()
                        
                    elif (_timedAccessInput.lower() == "false"):
                        _timedAccess = False
                    else:
                        print("[Start] Input not recognized, Exiting")
                        self.mainMenu()
                        
                    print("[Start] Gathered all information, please hold the tag onto the reader.")
                    _uid, _ident = _RFIDMANAGER.readRFID()
                    newIdent = str(secrets.token_urlsafe(30))
                    _identity = Identity(_nameInput, newIdent, _uid)
                    if(_DBMANAGER.identityAdd(_identity, _timedAccess, _timedStart, _timedStop)):
                        _RFIDMANAGER.writeRFID(newIdent)
                        print("[Start] Identity added successfully")
                        _LOCKMANAGER.appendLog("Identity '" + _nameInput + "' added with uid " + str(_uid))
                        _LOCKMANAGER.buzz(BuzzStatus.ACCESS_GRANTED)
                    else:
                        _LOCKMANAGER.buzz(BuzzStatus.ERROR)
                        print("[Start] Identity could not be added")
                    self.mainMenu()
                        
                except KeyboardInterrupt:
                    print("[Start] Identity add process interrupted.")
                    self.mainMenu()
            case "3":
                # Remove Identity
                print("[Start] Please enter the name of the identity that you want to remove")
                try:
                    _nameInput = input("Name: ")
                    if(_DBMANAGER.identityRemove(_nameInput)):
                        _LOCKMANAGER.buzz(BuzzStatus.ACCESS_GRANTED)
                        _LOCKMANAGER.appendLog("Identity '" + _nameInput + "' removed")
                        print("[Start] Identity removed")
                    else:
                        _LOCKMANAGER.buzz(BuzzStatus.ERROR)
                        print("[Start] Identity could not be removed")
                    self.mainMenu()
                        
                except KeyboardInterrupt:
                    print("[Start] Identity remove process interrupted.")
                    self.mainMenu()
                    
            case "4":
                # Disable Identity
                print("[Start] Please enter the name of the identity that you want to disable")
                try:
                    _nameInput = input("Name: ")
                    if(_DBMANAGER.setIdentityStatus(_nameInput, False)):
                        _LOCKMANAGER.buzz(BuzzStatus.ACCESS_GRANTED)
                        _LOCKMANAGER.appendLog("Identity '" + _nameInput + "' disabled")
                        print("[Start] Identity disabled")
                    else:
                        _LOCKMANAGER.buzz(BuzzStatus.ERROR)
                        print("[Start] Identity could not be disabled")
                    self.mainMenu()
                        
                except KeyboardInterrupt:
                    print("[Start] Identity disabling process interrupted.")
                    self.mainMenu()
                    
            case "5":
                # Enable Identity
                print("[Start] Please enter the name of the identity that you want to enable")
                try:
                    _nameInput = input("Name: ")
                    if(_DBMANAGER.setIdentityStatus(_nameInput, True)):
                        _LOCKMANAGER.buzz(BuzzStatus.ACCESS_GRANTED)
                        _LOCKMANAGER.appendLog("Identity '" + _nameInput + "' enabled")
                        print("[Start] Identity enabled")
                    else:
                        _LOCKMANAGER.buzz(BuzzStatus.ERROR)
                        print("[Start] Identity could not be enabled")
                    self.mainMenu()
                        
                except KeyboardInterrupt:
                    print("[Start] Identity enabling process interrupted.")
                    self.mainMenu()
                    
            case "6":
                # List Identities
                print("[Start] Now listing all identities")
                _DBMANAGER.printIdentities()
                input("Press enter to go back to menu")
                self.mainMenu()
                
            case "7":
                # Exit
                self.exit()
            case _:
                os.system('clear')
                print("WRONG COMMAND")
                self.mainMenu()

    def main(self):
        
        print("---------------------------------")
        print("- RFID Access Management System -")
        print("- by Megamezzomixer             -")
        print("---------------------------------")
        
        self.loadConfiguration()
        
        if (_DEBUG):
            print(
                "[DEBUG/Start] Debugging flag is ACTIVE. Disable it in the config if not needed."
            )

        if (_DBMANAGER.connectToDatabase()):
            if (_DEBUG):
                print("[DEBUG/Start] Database ready.")
        else:
            self.exit(1)

        # Test sequence
        if (_DEBUG):
            _LOCKMANAGER.buzz(BuzzStatus.TEST)
            _LOCKMANAGER.ledRed()
            _LOCKMANAGER.ledGreen()
            
        # Automated Reading
        if (len(sys.argv) >= 2):
            if (sys.argv[1].lower() == "--automated-reading"
                    or sys.argv[1].lower() == "-a"):
                
                print("[Start] Automated Reading activated")
                self.readMode()
        
        
        self.mainMenu()

if __name__ == "__main__":
    program = Start()
    program.main() # Non-static call of main needed in order to get full OOP running and being able to call Main Menu from other classes again in a non static way