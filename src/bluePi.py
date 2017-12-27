#!/usr/bin/python

# Source:
# https://www.raspberrypi.org/forums/viewtopic.php?p=619713#p619713

# Dependencies:
# sudo apt-get install -y python-gobject
# sudo apt-get install -y python-smbus
# sudo apt-get install -y python-dbus

#import signal
import dbus
import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
import logging

SERVICE_NAME = "org.bluez"
AGENT_IFACE = SERVICE_NAME + ".Agent1"
ADAPTER_IFACE = SERVICE_NAME + ".Adapter1"
DEVICE_IFACE = SERVICE_NAME + ".Device1"
PLAYER_IFACE = SERVICE_NAME + ".MediaPlayer1"
TRANSPORT_IFACE = SERVICE_NAME + ".MediaTransport1"

#LOG_LEVEL = logging.INFO
LOG_LEVEL = logging.DEBUG
LOG_FILE = "/dev/stdout"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"

class BluePlayer(dbus.service.Object):
	AGENT_PATH = "/blueplayer/agent"
	#Unit does not have display
	#Need to determine acutal capability
	CAPABILITY = "DisplayOnly"
	
if __name__ == "__main__":
	logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)
	logging.info("Starting BluePlayer")

	gobject.threads_init()
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

	player = None
	try:
		player = BluePlayer()
		mainloop = gobject.MainLoop()
		mainloop.run()
	except KeyboardInterrupt as ex:
		logging.info("BluePlayer canceled by user")
	except Exception as ex:
		logging.error("Unhandled error: {}".format(ex))
	#finally:
	#	if player:
	#		player.shutdown()
