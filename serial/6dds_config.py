import labrad.types as T

class AD9854(object):
    def __init__(self, **kwargs): #address, frequency, amplitude=1, clock_multiplier=24):
        self.freg = int(0x0b)
        self.areg = int(0x0c)
        for kw in kwargs:
            setattr(self, kw, kwargs[kw])
    
    def ftw(self):
        ftw = hex(int(self.frequency*2**32/self.sysclk))[2:].zfill(8) # 32-bit dac
        return [int('0x'+ftw[i:i+2], 0) for i in range(0, 8, 2)]

    def atw(self):
        atw =  hex(int(self.amplitude*(2**12-1)))[2:].zfill(4)
        return [int('0x'+self._atw(self.amplitude)[i:i+2], 0) for i in range(0, 4, 2)] + [0, 0]



class DDSConfig(object):
    def __init__(self):
        self.name = '%LABRADNODE% 6DDS Server'
        self.serial_server_name = 'vagabond_serial_server'
        self.port = '/dev/ttyACM0'
        self.timeout = T.Value(1, 's')
        self.baudrate = 9600
        self.stopbits=1
        self.bytesize=8

        self.update_id = 698017
        self.sweep_dwell = 1 # [s]

        self.dds = {
                     'dds0':              AD9854(address=0,
                                          state=True,
                                          frequency=80e6, # [Hz]
                                          frequency_range=(1e3, 140e6), # [Hz]
                                          amplitude=1,
                                          amplitude_range=(0, 1),
                                          sweepstate=False,
                                          sweeprate=1,  # [Hz/s]
                                          sweeprate_range=(-1000, 1000), # [Hz/s]
                                          sysclk=20e6),
                     }