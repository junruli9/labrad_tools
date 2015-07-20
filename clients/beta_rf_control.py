class RFControlConfig(object):
    def __init__(self):
        self.servername = 'yesr10_n5181a'
        self.name = 'beta'
        self.state_id = 461013
        self.frequency_id = 461014
        self.amplitude_id = 461015
        
        self.frequency_units = [(6, 'MHz')]
        self.frequency_digits = 3
        self.amplitude_units = [(0, 'dBm')]
        self.amplitude_digits = 2
        self.update_time = 100

        # widget sizes
        self.spinbox_width = 100


if __name__ == '__main__':
    from PyQt4 import QtGui
    from rf_control2 import CWControl
    a = QtGui.QApplication([])
    import qt4reactor 
    qt4reactor.install()
    from twisted.internet import reactor
    widget = CWControl('beta_rf_control', reactor)
    widget.show()
    reactor.run()
