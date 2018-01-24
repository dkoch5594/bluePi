#!/usr/bin/python

import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
import logging
import time

# Variables
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
LOG_FILE = "/dev/stdout"
#LOG_FILE = "path/to/some/log/file"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"

SERVICE_NAME = "org.bluez"

IFACES = {"AGENT" : SERVICE_NAME + ".Agent1",
	"AGENT_MANAGER" : SERVICE_NAME + ".AgentManager1",
	"ADAPTER" : SERVICE_NAME + ".Adapter1",
	"DEVICE" : SERVICE_NAME + ".Device1",
	"MEDIA_PLAYER" : SERVICE_NAME + ".MediaPlayer1",
	"MEDIA_TRANSPORT" : SERVICE_NAME + ".MediaTransport1" }
FD_DBUS = "org.freedesktop.DBus"
FD_PROPERTIES = FD_DBUS + ".Properties"

class TestPlayer(dbus.service.Object):

	def __init__(self):
		# Initialize bus
		self.bus = dbus.SystemBus()
		self.untrusted_devices = []
		# Retrieve adapter, properties and interface
		self.adapter_obj = self.getBusObject("ADAPTER")
		self.adapter_props = dbus.Interface(self.adapter_obj, FD_PROPERTIES)
		self.adapter = dbus.Interface(self.adapter_obj, IFACES["ADAPTER"])
		logging.info("Found adapter at {}".format(self.adapter_obj.object_path))

		# Initialize device handles
		self.dev_obj = None
		self.dev_props = None
		self.device = None
		
		# Register signalHanlder on the bus
		self.bus.add_signal_receiver(self.propertyChangeHandler
			, bus_name = SERVICE_NAME
			, dbus_interface = FD_PROPERTIES
			, signal_name = "PropertiesChanged"
			, path_keyword = "path")
		logging.info("Registered propertyChangeHandler")
		
		self.bus.add_signal_receiver(self.interfaceAddedHandler
			, bus_name = SERVICE_NAME
			,dbus_interface = FD_DBUS + ".ObjectManager"
			, signal_name = "InterfacesAdded")
		logging.info("Registered interfaceAddedHandler")

		# Turn adapter on
		self.adapter_props.Set(IFACES["ADAPTER"], "Powered", True)
		self.adapter_props.Set(IFACES["ADAPTER"], "Discoverable", True)

		self.findSource()

	
	def connectToSource(self, path, interfaces):
		success = False
		if IFACES["DEVICE"] not in interfaces:
			return success

		dev_obj = self.bus.get_object(SERVICE_NAME, path)
		dev_props = dbus.Interface(dev_obj, FD_PROPERTIES)
		if dev_props.Get(IFACES["DEVICE"], "Trusted") == False:
			return success

		device = dbus.Interface(dev_obj, IFACES["DEVICE"])
		try:
			device.Connect()
			success = True
			return success
		except dbus.exceptions.DBusException as ex:
			logging.error("Error [{}] while trying to connect to {}".format(ex, path))
			success = False
			return success

	def findSource(self):
		foundSource = False
		objects = self.getManagedObjects()
		for path, ifaces in objects.iteritems():
			foundSource = self.connectToSource(path, ifaces)
			if foundSource == True:
				break

		if foundSource == False:
			# Have iterated through existing devices, unable to connect to any
			# Start discovery
			self.adapter.StartDiscovery()	

	def getBusObject(self, name):
		objects = self.getManagedObjects()
		for path, ifaces in objects.iteritems():
			if IFACES[name] in ifaces:
				return self.bus.get_object(SERVICE_NAME, path)

	def getManagedObjects(self):
		obj_manager_obj = self.bus.get_object(SERVICE_NAME, "/")
		obj_manager = dbus.Interface(obj_manager_obj, FD_DBUS + ".ObjectManager")
		return obj_manager.GetManagedObjects()

	def interfaceAddedHandler(self, path, interfaces):
		logging.debug("Interface added at {}".format(path))
		self.connectToSource(path, interfaces)

	def propertyChangeHandler(self, interface, changed, invalidated, path):
		if interface == IFACES["DEVICE"]:
			if "Paired" in changed:
				if changed["Paired"] == True:
					logging.info("Paired with device at {}".format(path))
					dev_obj = self.bus.get_object(SERVICE_NAME, path)
					dev_props = dbus.Interface(dev_obj, FD_PROPERTIES)
					dev_props.Set(interface, "Trusted", True)
			if "Connected" in changed:
				if changed["Connected"] == True:
					if self.adapter_props.Get(IFACES["ADAPTER"], "Discovering") == True:
						self.adapter.StopDiscovery()
					self.dev_obj = self.bus.get_object(SERVICE_NAME, path)
					self.dev_props = dbus.Interface(self.dev_obj, FD_PROPERTIES)
					self.device = dbus.Interface(self.dev_obj, IFACES["DEVICE"])
					logging.info("Connected to device at {}".format(self.dev_obj.object_path))
				elif changed["Connected"] == False:
					logging.info("Disconnected from {}".format(self.dev_obj.object_path))
					self.dev_obj = None
					self.dev_props = None
					self.device = None
					self.findSource()
		elif interface == IFACES["ADAPTER"]:
			if "Powered" in changed:
				if changed["Powered"] == True:
					logging.info("Adapter powered on.")
			if "Discoverable" in changed:
				if changed["Discoverable"] == True:
					logging.info("Adapter is discoverable")
				elif changed["Discoverable"] == False:
					logging.info("Adapter is no loger discoverable")
			if "Discovering" in changed:
				if changed["Discovering"] == True:
					logging.info("Starting discovery")
				elif changed["Discovering"] == False:
					logging.info("Discovery Stopped")
	
	def shutdown(self):
		logging.info("Shutting down bluePlayer service")
		if self.adapter_props.Get(IFACES["ADAPTER"], "Discovering") == True:
			self.adapter.StopDiscovery()
		if self.device and self.dev_props.Get(IFACES["DEVICE"], "Connected") == True:
			self.device.Disconnect()
		self.adapter_props.Set(IFACES["ADAPTER"], "Discoverable", False)
		self.adapter_props.Set(IFACES["ADAPTER"], "Powered", False)

if __name__ == "__main__":
	# Configure Logging
	logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)
	
	# Set main loop as default (necessary for asynch calls/signals) 
	gobject.threads_init()
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	
	tp = None
	try:
		tp = TestPlayer()
		mainloop = gobject.MainLoop()
		mainloop.run()
	except KeyboardInterrupt:
		if tp:
			tp.shutdown()

