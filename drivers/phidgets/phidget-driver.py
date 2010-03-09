#!/usr/bin/env python
#-*- coding:utf-8 -*-
#
#    This file is part of Openplacos.
#
#    Openplacos is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Openplacos is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Openplacos.  If not, see <http://www.gnu.org/licenses/>.
#

# Generic
import logging
import time
import yaml
import os

# DBUS
import gobject
import dbus
import dbus.service
import dbus.glib

# Phidget specific imports
from Phidgets.Phidget import PhidgetLogLevel
from Phidgets.PhidgetException import *
from Phidgets.Events.Events import *
from Phidgets.Manager import *
from Phidgets.Devices.InterfaceKit import *
from Phidgets.Devices.TextLCD import *
from Phidgets.Devices.Encoder import *

# Constantes
CONF_BASE_PATH = '/org/openplacos/drivers/phidgets'
CONF_BASE_IFACE = 'org.openplacos.drivers.phidgets'

class PhidgetsDBUSDriver(dbus.service.Object):
    """
        Accès aux interfaces Phidgets
    """
    
    def __init__(self):
       
        self.logfile = "phidgets.log"

        bus_name = dbus.service.BusName(CONF_BASE_IFACE, bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, CONF_BASE_PATH )

        # les devices et les slots
        self.devices = []
        self.slots = []
        
        try:
            self.load_interfaces()
        except:
            logging.info("Erreur au chargement des intefaces Phidgets")
        else:
             logging.info("Interface(s) Phidgets chargée(s)")
    
    def load_interfaces(self):
        """
            Charge les interfaces définies dans le fichier de conf
        """
        # On charge la conf depuis un fichier YAML
        filename = "driver-conf.yml"
        try:
            f = open(filename, 'r')
            config = yaml.load(f.read())
            f.close()
        except:
            logging.debug("Erreur de lecture de la conf %s" % filename)
            raise NameError, "Load Config"
        
        for obj in config :
            # on instancie le type définit dans le yaml
            try:
                exec ("device = %s()" % (obj['type']) )
                device.enableLogging(PhidgetLogLevel.PHIDGET_LOG_VERBOSE, self.logfile)

                # callbacks
                device.setOnInputChangeHandler(self.__InputChange)
                device.setOnSensorChangeHandler(self.__SensorChange)
                device.setOnOutputChangeHandler(self.__OutputChange)
                
                device.setOnAttachHandler(self.phidget_attach_handler)
                device.setOnDetachHandler(self.phidget_detach_handler)
                device.openPhidget( obj['serial'])
                device.waitForAttach(2000)



            except:
                logging.debug("Erreur de création de l'interface %s" % obj['type'])
                raise NameError, "Create Config"
                
            # TODO : enlever les refs a waitForAttach()
            
        self.devices.append(device)
        return True
    
    
    def close(self):
        """
            Fermeture du driver
        """
        # on commence par fermer tous les phidgets ouverts : plus nécessaire apparement
        for phidget in self.devices:
            if phidget.isAttached():
                try:
                    phidget.closePhidget()
                except PhidgetException as e:
                    logging.debug ("Phidget Exception %i: %s" % (e.code, e.details))
                    print("Exiting....")
                    exit(1)

    ##
    ## Méthodes DBUS
    ##
    
    # d'abord le callback interne, appelle le signal DBUS
    def __InputChange(self, e):
            self.InputChange( e.device.getSerialNum(), e.index, e.value )
    
    @dbus.service.signal(dbus_interface='org.openplacos.drivers.phidgets', signature='iii')
    def InputChange(self, serial, index, value):
        print("InterfaceKit %i: Input %i: %s" % (serial, index, state))
        

    # d'abord le callback interne, appelle le signal DBUS
    def __OutputChange(self, e):
            self.OutputChange( e.device.getSerialNum(), e.index, e.state )

    @dbus.service.signal(dbus_interface='org.openplacos.drivers.phidgets', signature='iii')
    def OutputChange(self, serial, index, state):
            print("InterfaceKit %i: Output %i: %i" % (serial, index, state))
            
    
    # d'abord le callback interne, appelle le signal DBUS
    def __SensorChange(self, e):
            self.SensorChange( e.device.getSerialNum(), e.index, e.value )
                
    @dbus.service.signal(dbus_interface='org.openplacos.drivers.phidgets', signature='iii')
    def SensorChange(self, serial, index, value):
            print("InterfaceKit %i: Sensor %i: %i" % (serial, index, value))
            
        
    ##
    ## Phidgets Attach/Detach handlers
    ##
    def phidget_attach_handler(self, e):
        """ Handler de phidget attaché """
        attached = e.device
        print ("Attach %s : %s" % (attached.getDeviceType(), attached.getSerialNum() ) )
        # TODO : publier l'interface sur le bus
        # On crée un slot par E/S
        if attached.getDeviceType() == "PhidgetInterfaceKit" :
            # On crée les pins
            for i in range(0, attached.getOutputCount() ):
                print "Output %s created" % i
                self.slots.append(PhidgetDigitalOutput(attached, i ))
                
            for i in range(0, attached.getInputCount() ):
                print "Input %s created" % i
                self.slots.append(PhidgetDigitalInput(attached, i ))
                
            for i in range(0, attached.getSensorCount() ):
                print "Sensor %s created" % i
                self.slots.append(PhidgetAnalogInput(attached, i ))            
            
        elif attached.getDeviceType() == "PhidgetTextLCD" :
            # TODO : définir un objet TextLCD et l'instancier
            pass
    
    def phidget_detach_handler(self, e): 
        """ Handler de phidget détaché """
        detached = e.device
        print ("Detach %s : %s" % (detached.getDeviceType(), detached.getSerialNum() ) )
        # TODO : retirer l'interface du bus



class PhidgetDigitalOutput(dbus.service.Object):
    """
        Cette classe représente une sortie digitale d'une carte phidget
    """
    def __init__(self, interface, index):
        
        self.interface = interface
        self.index = index
        
        bus_name = dbus.service.BusName(CONF_BASE_IFACE, bus = dbus.SessionBus())
        path = '/org/openplacos/drivers/phidgets/%s/digital/output/%s' % (self.interface.getSerialNum(), index)
        dbus.service.Object.__init__(self, bus_name, path)

    @dbus.service.method('org.openplacos.api.digital', out_signature='b')
    def read(self):
        try: 
            value = self.interface.getOutputState(self.index)
        except PhidgetException as e:
            logging.debug("Phidget Exception %i: %s" % (e.code, e.details))
            return False
        return value

    @dbus.service.method('org.openplacos.api.digital', 'b')
    def write(self, value):
        try: 
            self.interface.setOutputState(self.index, value)
        except PhidgetException as e:
            logging.debug("Phidget Exception %i: %s" % (e.code, e.details))
            return False
        return True

class PhidgetDigitalInput(dbus.service.Object):
    """
        Cette classe représente une entrée digitale d'une carte phidget
    """

    def __init__(self, interface, index):
        
        self.interface = interface
        self.index = index
        
        bus_name = dbus.service.BusName(CONF_BASE_IFACE, bus = dbus.SessionBus())
        path = '/org/openplacos/drivers/phidgets/%s/digital/input/%s' % (self.interface.getSerialNum(), index)
        dbus.service.Object.__init__(self, bus_name, path)


    @dbus.service.method('org.openplacos.api.digital')
    def read(self):
        try: 
            value = self.interface.getInputState(self.index)
        except PhidgetException as e:
            logging.debug("Phidget Exception %i: %s" % (e.code, e.details))
            return False
        return value

    @dbus.service.method('org.openplacos.api.digital', 'b')
    def write(self, value):
        return False


class PhidgetAnalogInput(dbus.service.Object):
    """
        Cette classe représente une entrée analogique d'une carte phidget
    """
    def __init__(self, interface, index):
        
        self.interface = interface
        self.index = index
        
        bus_name = dbus.service.BusName(CONF_BASE_IFACE, bus = dbus.SessionBus())
        path = '/org/openplacos/drivers/phidgets/%s/analog/input/%s' % (self.interface.getSerialNum(), index)
        dbus.service.Object.__init__(self, bus_name, path)

    #
    # Interface générique analog
    #
    @dbus.service.method('org.openplacos.api.analog')
    def read(self):
        try: 
            value = self.interface.getSensorValue(self.index)
        except PhidgetException as e:
            logging.debug("Phidget Exception %i: %s" % (e.code, e.details))
            return False
        return value

    @dbus.service.method('org.openplacos.api.analog', 'i')
    def write(self, value):
        return False
        
    #
    # Interface spécifique phidgets
    #
    @dbus.service.method('org.openplacos.drivers.phidgets.analog')
    def setSensorChangeTrigger(self, value):
        """
            Règle le seuil de trigger de l'entrée analog
        """
        try:
            self.interface.setSensorChangeTrigger(self.index, value)
        except PhidgetException as e:
            logging.debug("Phidget Exception %i: %s" % (e.code, e.details))
            return False
        return value        
    

class PhidgetTextLCD(dbus.service.Object):
    """
        Cette classe permet d'accéder à un phidget TextLCD via DBus
    """
    def __init__(self, interface):
        
        self.interface = interface
        
        bus_name = dbus.service.BusName(CONF_BASE_IFACE, bus = dbus.SessionBus())
        path = '/org/openplacos/drivers/phidgets/%s/TextLCD' % self.interface.getSerialNum()
        dbus.service.Object.__init__(self, bus_name, path)
    


## En live..
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    driver = PhidgetsDBUSDriver()

    loop = gobject.MainLoop()
    print 'Listening'
    loop.run()

    driver.close()
    
