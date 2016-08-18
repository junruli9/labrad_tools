import json
import types
import inspect

from twisted.internet.defer import returnValue, inlineCallbacks
from labrad.server import LabradServer, setting

from decorators import quickSetting

def add_quick_setting(srv, ID, setting_name, arg_type):
    def setting(self, c, arg=None):
        pass
   
    setting.__name__ = str(setting_name)
    setting.__doc__ = "get or change {} ".format(setting_name)
    method = types.MethodType(setting, srv)
    qs = quickSetting(ID, arg_type)(method)
    setattr(srv, setting_name, qs)

def get_device_wrapper(device_config):
    device_type = device_config['device_type']
    module_path = 'devices.{}'.format(device_type.lower())
    module = __import__(module_path, fromlist=[device_type])
    return getattr(module, device_type)

def get_connection_wrapper(device):
    module_path = 'server_tools.connections.{}'.format(device.connection_type.lower())
    module = __import__(module_path, fromlist=[device.connection_type+'Connection'], level=1)
    return getattr(module, device.connection_type+'Connection')

class DeviceServer(LabradServer):
    def __init__(self, config_path='./config.json'):
        LabradServer.__init__(self)
        self.devices = {}
        self.open_connections = {}
        self.quick_settings = []

        self.load_config(config_path)
#        for i, (setting, arg_type) in enumerate(self.quick_settings):
#            add_quick_setting(self, 10 + i, setting, arg_type)

    def load_config(self, path=None):
        if path is not None:
            self.config_path = path
        with open(self.config_path, 'r') as infile:
            config = json.load(infile)
            for key, value in config.items():
                setattr(self, key, value)

    @inlineCallbacks
    def initServer(self):
        yield self.initialize_devices()

    @inlineCallbacks 
    def initialize_devices(self):
        for name, device in self.devices.items():
            device_wrapper = get_device_wrapper(device)
            device = device_wrapper(device)
            try: 
                connection_name = device.servername + ' - ' + device.address
                if connection_name not in self.open_connections:
                    connection = yield self.init_connection(device)
                    self.open_connections[connection_name] = connection
                device.connection = self.open_connections[connection_name]
                self.devices[name] = device
                yield device.initialize()
            except Exception, e:
                print e
                print 'could not initialize device {}'.format(name)
                print 'removing {} from available devices'.format(name)
                self.devices.pop(name)
    
    @inlineCallbacks
    def init_connection(self, device):
        connection = get_connection_wrapper(device)()
        yield connection.initialize(device)
        print 'connection opened: {} - {}'.format(device.servername, device.address)
        returnValue(connection)

    @setting(0, returns='s')
    def get_device_list(self, c):
        return json.dumps(self.devices.keys())
    
    @setting(1, name='s', returns='s')
    def select_device(self, c, name):
        if name not in self.devices.keys():
            message = '{} is not the name of a configured device'.format(name)
            raise Exception(message)
        
        c['name'] = name
        device = self.get_device(c)
        return json.dumps(device.__dict__, default=lambda x: None)

    def get_device(self, c):
        name = c.get('name')
        if name is None:
            raise Exception('select a device first')
        return self.devices[name]

    @setting(2)
    def send_update(self, c):
        device = self.get_device(c)
        update = {c['name']: {p: getattr(device, p) 
                  for p in device.update_parameters}}
        yield self.update(json.dumps(update))