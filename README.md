# RFID Access Management System (RAMS)
The RAMS is a python-based physical lock software with built in identity management, developed for the Raspberry Pi.
It's main purpose is to be used at doors or lockable cabinets, drawers, basically anything that an electric or magnetic lock can be installed at.

# Features
RAMS offers a wide variety of options, such as...

 - Identity adding/removal
 - Per-Identity Timed Access (e.g. Access from 10:00 - 14:00)
 - Two-Stage Tag Authentication*
 - Easy-to-edit settings using a simple config file
 - Access and Identity Management Logging
 - Optional Debug Mode
 - Following GPIO Pins are supported: 
	 - Red LED Pin
	 - Green LED
	 - Passive Buzzer
	 - Lock
- Easy-to-use Administration Panel

(* The currently used "MIFARE Classic" Tags are considered as **not secure** and should not be used in security-dependent environments.)
# Requirements

 - Raspberry Pi
	 - 4 GPIO Pins (configurable. 05, 06, 13 and 19 by default)
 - MFRC522 RFID Reader/Writer
	 - Enough MFRC522 chips
 - Python **3.10** or higher
 - Python Modules:
	 - SimpleMFRC522
	 - GPIOZero
	 - MySQLConnector
	 - PrettyTable
 - MySQL-Like Database
