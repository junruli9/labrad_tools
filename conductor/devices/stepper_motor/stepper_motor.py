import sys
sys.path.append('../')
from generic_device.generic_parameter import GenericParameter

from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync


class Position(GenericParameter):
    def __init__(self, config):
        super(Position, self).__init__(config)
        self.value = 2200

    @inlineCallbacks
    def initialize(self):
        self.cxn = yield connectAsync()
        yield self.cxn.stepper_motor.select_device('nd_filter')
    
    @inlineCallbacks
    def update(self, value):
        yield self.cxn.stepper_motor.move_absolute(value)
