"""
### BEGIN NODE INFO
[info]
name = stepper_device
version = 1.0
description = 
instancename = stepper_device

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import json
import sys

from labrad.server import Signal, setting
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

sys.path.append('../')
from serial_device_server import SerialDeviceServer

UPDATE_ID = 698021

class StepperMotorServer(SerialDeviceServer):
    update = Signal(UPDATE_ID, 'signal: update', 's')

    @setting(2, 'move absolute', position='i', returns='b')
    def move_absolute(self, c, position=None):
        device = self.get_device(c)
        if position is not None:
            yield device.move_absolute(position)
        returnValue(device.position)

if __name__ == "__main__":
    from labrad import util
    util.runServer(StepperMotorServer())
