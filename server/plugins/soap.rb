#!/usr/bin/ruby -w

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

require 'dbus'
require 'rubygems'
require "soap/rpc/standaloneServer"

if File.symlink?(__FILE__)
  P =  File.dirname(File.readlink(__FILE__))
else 
  P = File.expand_path(File.dirname(__FILE__))
end
a = P.split("/")
PATH = a.slice(0..a.rindex("openplacos")).join("/")


if(ENV['DEBUG_OPOS'] ) ## Stand for debug
  clientbus =  DBus::SessionBus.instance
else
  clientbus =  DBus::SystemBus.instance
end

serv = clientbus.service("org.openplacos.server")

plugin = serv.object("/plugins")
plugin.introspect
plugin.default_iface = "org.openplacos.plugins"

plugin.on_signal("quit") do
  Process.exit(0)
end

plugin.on_signal("ready") do
  Thread.new do
    Thread.abort_on_exception = true
    require "#{PATH}/client/libclient/libclient.rb"


    begin
       class MySoapServer < SOAP::RPC::StandaloneServer

          # Expose our services
          def initialize(opos_,*args)
            @opos = opos_
            super(*args)
             add_method(self, 'sensors')
             add_method(self, 'actuators')
             add_method(self, 'actuators_methods','path')
             add_method(self, 'objects')
             add_method(self, 'get','path')
             add_method(self, 'set_a','path','meth')  #cant use set for methode name
          end
          
          def sensors
            @opos.sensors.keys
          end
        
          def actuators
            @opos.actuators.keys
          end
          
          def actuators_methods(path)
            @opos.actuators[path].methods.keys
          end
         
          def objects
            @opos.objects.keys
          end
          
          def get(path)
            @opos.sensors[path].value[0]
          end

          def set_a(path,meth)
            @opos.actuators[path].method(meth).call
          end

      end
      
      opos = LibClient::Server.new
      port = 8081
      server = MySoapServer.new(opos,"MySoapServer", 
                'urn:ruby:opos', '0.0.0.0', port)
      server.start
    rescue => err
      puts err.message
    end       
    
  end
end 
plugin.plugin_is_ready("soap.rb")
main = DBus::Main.new
main << clientbus
main.run


