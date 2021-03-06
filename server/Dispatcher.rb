#    This file is part of Openplacos.
#
#    Openplacos is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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

require 'Wire.rb'

class Dispatcher
  include Singleton

  def init_dispatcher # act as a constructor
    @wires         = Array.new
    @pins          = Array.new
    @binding       = Hash.new
    @iface_inherit = Hash.new
  end
  
  def add_wire(wire_config_)
    @wires << Wire.new(wire_config_)
  end
  
  def register_pin(pin_)
    @pins << pin_
    @binding[pin_.dbus_name]  = Array.new
    push_pin(pin_)
  end
  
  def push_pin (pin_)
    @wires.each do |wire|
      wire.push_pin(pin_) # Maybe pin_ is part of wire
    end
  end

  def check_all_pin # Check that every wire has to 2 pins
     @wires.each do |wire|
      wire.check_pins 
      @binding[wire.pin0.dbus_name]       << wire.pin1
      @iface_inherit[wire.pin0.dbus_name] = wire.pin1.match_iface(wire.pin0) # push here iface to use
      @binding[wire.pin1.dbus_name]       << wire.pin0
      @iface_inherit[wire.pin1.dbus_name] = wire.pin0.match_iface(wire.pin1) # push here iface to use
    end
  end

  # return true if pin_name is bind 
  def is_bind?(pin_name)
    @binding.has_key?(pin_name) &&  !@binding[pin_name].empty?
  end

  def call(pin_sender_name_, iface_, method_, *args_) 
    # Set iface to mapping inherited iface  
    if(@iface_inherit[pin_sender_name_][iface_].nil?)
      iface = iface_
    else
      iface = @iface_inherit[pin_sender_name_][iface_]
    end

    @binding[pin_sender_name_].each { |pin|
      if pin.interfaces.include?(pin.get_iface(iface))
        return pin.method_exec(iface, method_, *args_)
      end
    }
    Globals.error("No mapping found at runtime", 42)
  end

  def get_plug(dbus_name_) #return an array of plugged pin
    return @binding[dbus_name_]
  end

  def get_plugged_ifaces(dbus_name_)
    ifaces = Array.new
    get_plug(dbus_name_).each do |pin|
      ifaces << pin.config.keys 
    end
    ifaces.flatten
  end
end

