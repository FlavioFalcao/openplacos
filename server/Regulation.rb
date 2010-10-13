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

class Regulation
  
  attr_reader :action_down, :action_up
  
  def initialize(config_,measure_)
      
      @measure     = measure_
      @action_up   = config_["action+"]
      @action_down = config_["action-"]
      @is_regul_on = false
      @order       = nil
      Thread.abort_on_exception = true
      
      @thread = Thread.new{
        Thread.stop
        loop do
          sleep(1)
          puts "regulation #{@measure.name} : #{@measure.get_value()} "
          #regul(nil)
        end
      }  
      @thread.wakeup
  end
  
  
  def regul(option_)

    #while(@is_regul_on)
      #sleep 1
      puts "regulation #{@measure.name} : #{@measure.get_value()} "
    #end

  end
  
  def set(option_)
    @is_regul_on = true
    @thread.wakeup
  end
  
  def unset
    @is_regul_on = false
  end

end
