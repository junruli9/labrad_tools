from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal 
from connection import connection
from twisted.internet.defer import inlineCallbacks
import numpy as np
import json
from client_tools import SuperSpinBox

class AnalogVoltageManualControl(QtGui.QGroupBox):
    hasNewVoltage = False
    mouseHover = pyqtSignal(bool)
    layout = None

    def __init__(self, configuration, reactor, cxn=None):
        QtGui.QDialog.__init__(self)
        self.reactor = reactor
        self.cxn = cxn 
        self.load_control_configuration(configuration)
        self.connect()

    def load_control_configuration(self, configuration):
        for key, value in configuration.__dict__.items():
            setattr(self, key, value)

    @inlineCallbacks
    def connect(self):
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            yield self.get_server_configuration()
            self.populateGUI()
            yield self.connectSignals()
            yield self.requestValues()
        except Exception, e:
            print e
            self.setDisabled(True)

    @inlineCallbacks
    def get_server_configuration(self):
        self.voltage_range = (-10., 10.)
        yield None
#        server = yield self.cxn.get_server(self.servername)
#        serverconf_str = yield server.get_configuration()
#        for key, value in json.loads(serverconf_str).items():
#            setattr(self, key, value)
    
    def populateGUI(self):
        self.mode_button = QtGui.QPushButton()
        self.mode_button.setCheckable(1)
        self.mode_button.setFixedWidth(self.spinbox_width)
        
        self.voltage_box = SuperSpinBox(self.voltage_range, self.voltage_units, self.voltage_digits)
        self.voltage_box.setFixedWidth(self.spinbox_width)
        self.voltage_box.display(0)

        if self.layout is None:
            self.layout = QtGui.QGridLayout()

        self.layout.addWidget(QtGui.QLabel('<b>'+self.name+'</b>'), 1, 0, 1, 1, QtCore.Qt.AlignHCenter)
        self.layout.addWidget(self.mode_button, 1, 1)
        self.layout.addWidget(QtGui.QLabel('Voltage: '), 2, 0, 1, 1, QtCore.Qt.AlignRight)
        self.layout.addWidget(self.voltage_box, 2, 1)
        self.setLayout(self.layout)
        self.setFixedSize(100 + self.spinbox_width, 70)

    @inlineCallbacks
    def connectSignals(self):
        server = yield self.cxn.get_server(self.servername)
        yield server.signal__update(self.update_id)
        yield server.addListener(listener=self.receive_update, source=None, ID=self.update_id)
        yield self.cxn.add_on_connect(self.servername, self.reinitialize)
        yield self.cxn.add_on_disconnect(self.servername, self.disable)

        self.mode_button.released.connect(self.onNewMode)
        self.voltage_box.returnPressed.connect(self.onNewVoltage)
        self.setMouseTracking(True)
        self.mouseHover.connect(self.requestValues)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.writeValues)
        self.timer.start(self.update_time)

    @inlineCallbacks
    def requestValues(self, c=None):
        server = yield self.cxn.get_server(self.servername)
        yield server.notify_listeners()

    def receive_update(self, c, signal):
        self.free = False
        signal = json.loads(signal)
        for s in signal:
            if signal[s]['name'] == self.name:
                update = signal[s]
        print update
        if update['mode'] == 'manual':
            self.mode_button.setChecked(1)
            self.mode_button.setText('Manual')
        else:
            self.mode_button.setChecked(0)
            self.mode_button.setText('Auto')
        self.voltage_box.display(update['manual voltage'])
        self.free = True

    def enterEvent(self, c):
        self.mouseHover.emit(True)

    def leaveEvent(self, c):
        self.mouseHover.emit(True)

    @inlineCallbacks
    def onNewMode(self):
        if self.free:
            server = yield self.cxn.get_server(self.servername)
            mode = yield server.channel_mode(self.name)
            if mode == 'manual':
                yield server.channel_mode(self.name, 'auto')
            else:
                yield server.channel_mode(self.name, 'manual')

    @inlineCallbacks
    def writeValues(self):
        if self.hasNewVoltage:
            server = yield self.cxn.get_server(self.servername)
            yield server.channel_manual_voltage(self.name, self.voltage_box.value())
            self.hasNewVoltage = False
    
    def onNewVoltage(self):
        if self.free:
            self.hasNewVoltage = True
                
    @inlineCallbacks
    def reinitialize(self):
        pass

    def disable(self):
        self.setDisabled(True)

    def closeEvent(self, x):
        self.reactor.stop()

class ControlConfig(object):
    def __init__(self):
        self.name = 'MOT Coil'
        self.servername = 'yesr20_analog_sequencer'
        self.update_id = 461023
        self.update_time = 100 # [ms]

        self.voltage_units = [(0, 'V')]
        self.voltage_digits = 3
        self.spinbox_width = 80

if __name__ == '__main__':
    a = QtGui.QApplication([])
    import qt4reactor 
    qt4reactor.install()
    from twisted.internet import reactor
    widget = AnalogVoltageManualControl(ControlConfig(), reactor)
    widget.show()
    reactor.run()
