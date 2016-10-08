import sys
sys.path.append('../')
from generic_device.generic_parameter import GenericParameter

from twisted.internet.defer import inlineCallbacks
from labrad.wrappers import connectAsync

from lib.helpers import get_measurements

class Frac(GenericParameter):
    def value(self):
        return get_measurements()['frac']


        
