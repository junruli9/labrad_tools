import json
import types

import ok
from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread

from okfpga.sequencer.sequence import Sequence

class ConductorServer(LabradServer):
    name = '%LABRADNODE% Conductor'
    def __init__(self, config_name):
        self.device_parameters = {}
        self.sequence_parameters = {}
        self.sequence = {}
        LabradServer.__init__(self)
        self.config_name = config_name
        self.load_configuration()
        self.in_communication = DeferredLock()
	self.update = Signal(self.update_id, 'signal: update', 's')

    @inlineCallbacks
    def initServer(self):
        yield LabradServer.initServer(self)
        yield self.run_sequence()

    def load_configuration(self):
        config = __import__(self.config_name).ConductorConfig()
        for key, value in config.__dict__.items():
            setattr(self, key, value)

    @setting(1, 'set device parameters', device_parameters='s', returns='s')
    def set_device_parameters(self, c, device_parameters=None):
        """ 
        device parameters is "{*device_name: {*parameter_name: {command: *command, value: *value}}}"
        *command is something like "lambda value: sever_name.setting(value)"
        """
        device_parameters = json.loads(device_parameters)
        if device_parameters is not None:
            self.initialize_device_parameters(device_parameters)
            self.device_parameters.update(device_parameters)
        return json.dumps(self.device_parameters)

    def initialize_device_parameters(self, device_parameters):
        value = None
        for device, parameters in device_parameters.items():
            for p, d in parameters.items():
                if type(d['value']) is types.ListType:
                    value = d['value'][0]
                else:
                    value = d['value']
            self = self
            eval(d['init command'])
            eval(d['command'])(value)

    @setting(2, 'set sequence parameters', sequence_parameters='s', returns='s')
    def set_sequence_parameters(self, c, sequence_parameters=None):
        """
        parameters is dictionary {name: value}
        """
        sequence_parameters = json.loads(sequence_parameters)
        if sequence_parameters is not None:
            self.sequence_parameters = sequence_parameters
        self.update(json.dumps(self.sequence_parameters))
        return json.dumps(self.sequence_parameters)

    @setting(3, 'load sequence', sequence='s', returns='s')
    def load_sequence(self, c, sequence):
        sequence_keyfix = {}
        for sequencer in self.sequencers:
            server = getattr(self.client, sequencer)
            s = yield server.fix_sequence_keys(sequence)
            sequence_keyfix.update(s)
        self.sequence = Sequence(sequence_keyfix)
        returnValue(self.sequence.dump())

    def evaluate_sequence_parameters(self, sequence):
        next_parameters = {}
        for p, v in self.sequence_parameters.items():
            if type(v) is types.ListType:
                next_parameters[p] = v[0]
                v.insert(len(v), v.pop(0))
            else:
                next_parameters[p] = v
        next_sequence = sequence.dump()
        for p, v in next_parameters:
            next_sequence.replace('"'+p+'"', str(v))
        return next_sequence

    @inlineCallbacks
    def evaluate_device_parameters(self):
        value = None
        for device, parameters in self.device_parameters.items():
            for p, d in parameters.items():
                if type(d['value']) is types.ListType:
                    value = d['value'][0]
                    d['value'].insert(len(d['value']), d['value'].pop(0))
                else:
                    value = d['value']
                self = self
                yield eval(d['command'])(value)
                print value
    
    @inlineCallbacks
    def run_sequence(self):
        yield self.evaluate_device_parameters()
        if self.sequence:
            sequence = self.evaluate_sequence_parameters(self.sequence)
            for sequencer in self.sequencers:
                server = getattr(self.client, sequencer)
                self.in_communication.acquire()
                yield None
#                yield server.run_sequence(sequence)
                self.in_communication.release()
            reactor.callLater(self.sequence.get_duration(), self.run_sequence)
        else:
            reactor.callLater(5, self.run_sequence)

if __name__ == "__main__":
    config_name = 'conductor_config'
    __server__ = ConductorServer(config_name)
    from labrad import util
    util.runServer(__server__)
