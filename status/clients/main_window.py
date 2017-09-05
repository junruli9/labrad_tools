import json
import time
import numpy as np
import os
import sys

import client_config

sys.path.append('../../client_tools')
sys.path.append('../../arduino/clients')
sys.path.append('../../conductor/clients')

sys.path.append('../../sequencer/clients')

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from twisted.internet.defer import inlineCallbacks

SEP = os.path.sep

from status_client import StatusClient
from arduino_client import ArduinoClient
from parameter_values_control import ParameterControl, ControlConfig
from sequencer_control import SequencerControl

# Runs the indicator button and communicates with Labrad servers
class MainClient(QMainWindow):
    RAD = client_config.widget['rad']

    def __init__(self, reactor, parent=None):
        super(MainClient, self).__init__(parent)
        self.reactor = reactor
        self.setGeometry(0, 0, 3*self.RAD, 3*self.RAD)
        self.alive = True
        self.state = -1
        
        # layout the GUI
        self.setupLayout()

    # Lays out the widget
    def setupLayout(self):
        self.setWindowTitle('Main Widget')
        #create a vertical layout
        # add the indicator to the widget and connect signals
        self.status_widget = StatusClient(self.reactor)

        self.arduino_widget = QDockWidget()
        arduino_title = QLabel()
        arduino_title.setText('Arduino')
        arduino_title.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.arduino_widget.setTitleBarWidget(arduino_title)
        self.arduino_widget.setWidget(ArduinoClient(self.reactor))
        
        pvc_title = QLabel()
        pvc_title.setText('Variables Control')
        pvc_title.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.parameter_widget = QDockWidget()
        self.parameter_widget.setTitleBarWidget(pvc_title)
        self.parameter_widget.setWidget(ParameterControl(ControlConfig(), self.reactor))

        self.sequencer_widget = QDockWidget()
        self.sequencer_widget.setWidget(SequencerControl(self.reactor))

        self.setCentralWidget(self.status_widget)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.arduino_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.parameter_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.sequencer_widget)

    def closeEvent(self, x):
        #stop the reactor when closing the widget
        self.alive = False
        self.reactor.stop()

# Starts the widget
if  __name__ == '__main__':
    a = QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = MainClient(reactor)
    widget.show()
    reactor.run()
