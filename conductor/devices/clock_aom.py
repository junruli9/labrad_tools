from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync

class Frequency(object):
    def __init__(self):
        self.priority = 1
        self.value_type = 'single'
        self.value = None

    @inlineCallbacks
    def initialize(self):
        self.cxn = yield connectAsync()
        yield self.cxn.rf.select_device('clock_steer')
    
    @inlineCallbacks
    def stop(self):
        yield None

    @inlineCallbacks
    def update(self, value):
        ans = yield self.cxn.rf.frequency(value)
