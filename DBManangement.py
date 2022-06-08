import datetime
from enum import Enum
import os
import secrets
import mysql.connector
import configparser
from prettytable import PrettyTable, from_db_cursor

from mysql.connector import errorcode

from Identity import Identity


class DatabaseManager:

    def _loadConfiguration(self):
        config = configparser.ConfigParser()
        if os.path.exists("config.ini"):
            config.read("config.ini")
            global _DEBUG
            _DEBUG = config["General"].getboolean("Debug")

            global _DBHOST
            _DBHOST = config["Database"]["Host"]
            global _DBUSER
            _DBUSER = config["Database"]["Username"]
            global _DBPASS
            _DBPASS = config["Database"]["Password"]
            global _DBNAME
            _DBNAME = config["Database"]["Name"]
            global _DBPORT
            _DBPORT = config["Database"].getint("Port")
            
    def disconnect(self):
        if ("_con" in globals()):
            _con.close()
            print("[DBManagement] MySQL-Database disconnected")
        else:
            if (_DEBUG):
                print(
                    "[DEBUG/DBManagement] Couldn't disconnect Database as the connector object wasn't initialized"
                )
                
    def connectToDatabase(self):
        if (_DEBUG):
            print("[DEBUG/DBManagement] Connecting to the MySQL-Database...")
        try:
            global _con
            _con = mysql.connector.connect(host=_DBHOST,
                                           user=_DBUSER,
                                           password=_DBPASS,
                                           database=_DBNAME,
                                           port=_DBPORT)
            
            _con.autocommit = True
            self._populateDatabase()
            
        except mysql.connector.Error as err:
            print("[DBManagement] " + err.msg)
            return False
        return True
    
    def _populateDatabase(self):
        try:
            cursor = _con.cursor()
            query = "SHOW TABLES LIKE 'userdata'"
            cursor.execute(query)
            result = cursor.fetchone()
            if (result):
                return  # DB Exists, so don't bother creating or populating
            
            print("[DBManagement] Making Database ready for first use...")
            # Populate database
            query = '''CREATE TABLE userdata (
            uid BIGINT NOT NULL,
            name VARCHAR(20) NOT NULL UNIQUE,
            identifier VARCHAR(40) NOT NULL UNIQUE,
            timeRestricted BOOLEAN NOT NULL,
            enabled BOOLEAN NOT NULL,
            timeframeStart TINYINT,
            timeframeEnd TINYINT,
            PRIMARY KEY(uid))'''
            
            cursor.execute(query)
            print("[DBManagement] Done! Resuming normal operation")
            
        except mysql.connector.Error as err:
            print("[DBManagement] Failed populating database: {}".format(err))
            raise mysql.connector.Error("Failed to create Database")
        
    def checkIdentity(self, identity: Identity):
        try:
            query = "SELECT name, identifier, timeRestricted, enabled, timeframeStart, timeframeEnd FROM userdata WHERE uid = %s;"
            cursor = _con.cursor()
            identityUID = identity.getUID()
            identityIdentifier = identity.getIdent()
            cursor.execute(query, (identityUID, ))
        except Exception as err:
            print("[DBManagement] Error: " + err.msg)
            cursor.close()
            return False, AccessStatus.DATABASE_ERROR
        
        for (name, identifier, timeRestricted, enabled, timeframeStart,
             timeframeEnd) in cursor:
            identity.setName(name) # Trying to set the uids corresponding name to make logging more accurately 
            
            if (enabled == 0):
                cursor.close()
                return False, AccessStatus.IDENT_DISABLED # Identity is disabled within the database
            
            if (identifier == None or secrets.compare_digest(identifier, identityIdentifier) == False):
                cursor.close()
                return False, AccessStatus.IDENT_WRONG_KEY # Identifier is either nonexistant or not matching with the database one
            
            if (not timeRestricted):
                cursor.close()
                return True, AccessStatus.GRANTED
            
            if(timeRestricted and (timeframeStart == None or timeframeEnd == None)):
                cursor.close()
                return False, AccessStatus.NOT_IN_TIMEFRAME # Database has no timeframe saved, but the chip has timed access enabled
            
            currentTime = datetime.datetime.now()
            if(_DEBUG and timeRestricted):
                print("[DEBUG/DBManagement] Timeframe start equation result: " + str(currentTime.hour - timeframeStart) + " Timeframe End equation result: " + str(timeframeEnd - currentTime.hour))
                
            if(currentTime.hour - timeframeStart >= 0 and timeframeEnd - currentTime.hour >= 0): # Timeframe calculation current hour subtracted by the timeframe start and timeframe end subtracted by the current hour
                cursor.close()
                return True, AccessStatus.GRANTED # Both timeframes are in positive value, therefore its within timeframe
            else:
                cursor.close()
                return False, AccessStatus.NOT_IN_TIMEFRAME # At least one of the values are 0 or negative, therefore not within timeframe
            
        cursor.close()
        return False, AccessStatus.IDENT_UNKNOWN # No above condition was true

    def identityAdd(self, identity: Identity, timeRestricted: bool = False, accessTimeStart: int = None, accessTimeEnd: int = None):
        if(accessTimeStart != None and accessTimeEnd != None):
            if(accessTimeStart < 0 or accessTimeStart > 23):
                print("[DBManagement] Could not add Identity: accessTimeStart must range between 0 and 23")
                return False
            if(accessTimeEnd < 1 or accessTimeEnd > 24):
                print("[DBManagement] Could not add Identity: accessTimeEnd must range between 1 and 24")
                return False
            if(accessTimeStart >= accessTimeEnd):
                print("[DBManagement] Could not add Identity: accessTimeStart cannot be higher or equal as accessTimeEnd")
                return False
        try:
            query = "INSERT INTO userdata (uid, name, identifier, timeRestricted, enabled, timeframeStart, timeframeEnd) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor = _con.cursor()
            identityUID = identity.getUID()
            identityName = identity.getName()
            identityKey = identity.getIdent()
            cursor.execute(query, (identityUID, identityName, identityKey, timeRestricted, True, accessTimeStart, accessTimeEnd))
            _con.commit()
            cursor.close()
            return True
        except mysql.connector.Error as err:
            if(err.errno == 1062):
                print("[DBManagement] Error: Identity or tag ID already exists")
            else:
                print("[DBManagement] Error: " + err.msg)
            cursor.close()
            return False
            
    def identityRemove(self, name: str):
        try:
            if(name.__len__() > 30): # We only have 30 digits space in the Database for the name, hence the precheck
                print("Input too long")
                return False
            # Check if identity exists
            cursor = _con.cursor()
            query = "SELECT uid FROM userdata WHERE name = %s"
            cursor.execute(query, (name,))
            result = cursor.fetchone()
            if(result == None):
                print("[DBManagement] Identity doesn't exist")
                cursor.close()
                return False
            
            #executing removal
            query = "DELETE FROM userdata WHERE name = %s"
            cursor.execute(query, (name,))
            _con.commit()
            cursor.close()
            return True
            
        except mysql.connector.Error as err:
            print("[DBManagement] Error: " + err.msg)
            cursor.close()
            return False
            
        
    def setIdentityStatus(self, name: str, status:bool):
        try:
            if(name.__len__() > 30): # We only have 30 digits space in the Database for the name, hence the precheck
                print("Input too long")
                return False
            # Check if identity exists
            cursor = _con.cursor()
            query = "SELECT enabled FROM userdata WHERE name = %s"
            cursor.execute(query, (name,))
            result = cursor.fetchone()
            if(result == None):
                print("[DBManagement] Identity doesn't exist")
                cursor.close()
                return False
            if(result == status):
                print("[DBManagement] Identity enabled status already set to " + str(status))
                cursor.close()
                return False
            
            
            # Perform enable/disable
            cursor = _con.cursor()
            query = "UPDATE userdata SET enabled=%s WHERE name = %s"
            cursor.execute(query, (status, name))
            _con.commit()
            cursor.close()
            return True
            
        except mysql.connector.Error as err:
            print("[DBManagement] Error: " + err.msg)
            cursor.close()
            return False
        
    def printIdentities(self):
        try:
            cursor = _con.cursor()
            query = "SELECT * FROM userdata WHERE 1"
            cursor.execute(query)
            table = from_db_cursor(cursor)
            print(table)
            cursor.close()
            
        except mysql.connector.Error as err:
            print("[DBManagement] Error: " + err.msg)
            cursor.close()
            return False
        
    def __init__(self):
        self._loadConfiguration()
        
        
class AccessStatus(Enum):
    GRANTED = 0
    NOT_IN_TIMEFRAME = 1
    IDENT_DISABLED = 2
    IDENT_UNKNOWN = 3
    DATABASE_ERROR = 4
    IDENT_WRONG_KEY = 5
