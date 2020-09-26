"""
### BEGIN NODE INFO
[info]
name = hv_interlock
version = 1.0
description = 
instancename = hv_interlock

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

class HVInterlockServer(LabradServer):
    name = 'hv_interlock'

    def __init__(self, config_path='./config.json'):
        super(HVInterlockServer, self).__init__()
        # connect to Arduino 

    @setting(1, returns='v')
    def get_voltage(self, c):
        pass

    @setting(2)
    def enable_output(self, c, enable):
        pass

    
if __name__ == "__main__":
    from labrad import util
    util.runServer(HVInterlockServer())
