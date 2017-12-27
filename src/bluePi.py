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

def getManagedObjects():
	bus = dbus.SystemBus()
	manager = dbus.Interface(bus.get_object(SERVICE_NAME, "/"), "org.freedesktop.DBus.ObjectManager")
	return manager.GetManagedObjects()

def findAdapter():
	objects= getManagedObjects()
	bus = dbus.SystemBus()
	for path, ifaces in objects.iteritems():
		adapter = ifaces.get(ADAPTER_IFACE)
		if adapter is None:
			continue
		obj = bus.get_object(SERVICE_NAME, path)
		return dbus.Interface(obj, ADAPTER_IFACE)
	raise Exception("Bluetooth adapter not found")

class BluePlayer(dbus.service.Object):
	AGENT_PATH = "/blueplayer/agent"
	#Unit does not have display
	#Need to determine acutal capability
	CAPABILITY = "DisplayOnly"
	
	bus = None
	adapter = None
	device = None
	deviceAlias = None
	player = None
	transport = None
	connected = None
	state = None
	status = None
	discoerable = None
	track = None
	
	def __init__(self):
		# Initialize gobject and find any current media players
		self.bus = dbus.SystemBus()

		dbus.service.Object.__init__(self, self.bus(), BluePlayer.AGENT_PATH)

		self.bus.add_signal_receiver(self.playerHandler,
			bus_name = SERVICE_NAME,
			dbus_interface = "org.freedesktop.DBus.Properties",
			signal_name = "PropertiesChanged",
			path_keyword = "path")

		self.registerAgent()

		adapter_path = findAdapter().object_path
		self.bus.add_signal_receiver(self.adapterHandler,
			bus_name = SERVICE_NAME,
			path = adapter_path,
			dbus_interface = "org.freedesktop.DBus.Properties",
			signal_name = "PropertiesChanged",
			path_keyword = "path")

		self.findPlayer()

	
"""
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
"""
