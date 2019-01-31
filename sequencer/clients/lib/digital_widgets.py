from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal 
import numpy as np
import json
import matplotlib
matplotlib.use('Qt4Agg')

class Spacer(QtGui.QFrame):
    def __init__(self, config):
        super(Spacer, self).__init__(None)
        self.setFixedSize(config.spacer_width, config.spacer_height)
        self.setFrameShape(1)
        self.setLineWidth(0)

class SequencerButton(QtGui.QFrame):
    # added KM 05/07/18
    changed_signal = QtCore.pyqtSignal()
    # added KM 1/23/19
    clicked_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super(SequencerButton, self).__init__(None)
        self.setFrameShape(2)
        self.setLineWidth(1)
        self.on_color = '#ff69b4'
        self.off_color = '#ffffff'
        self.name = ''

    def setChecked(self, state):
        if state:
            self.setFrameShadow(0x0030)
            self.setStyleSheet('QWidget {background-color: %s}' % self.on_color)
            self.is_checked = True
        else:
            self.setFrameShadow(0x0020)
            self.setStyleSheet('QWidget {background-color: %s}' % self.off_color)
            self.is_checked = False
        # added KM 05/07/18
        self.changed_signal.emit()

    def changeState(self):
        if self.is_checked:
            self.setChecked(False)
        else:
           self.setChecked(True)

    # modified KM 1/23/19
    def mousePressEvent(self, event):
        self.changeState()
        self.clicked_signal.emit(self.name)
        event.accept()


class DigitalColumn(QtGui.QWidget):

    # added KM 1/23/19
    clicked_signal = pyqtSignal(str,int)

    def __init__(self, channels, config, position):
        super(DigitalColumn, self).__init__(None)
        self.channels = channels
        self.config = config
        self.position = position
        self.populate()

    def populate(self):
        self.buttons = {nl: SequencerButton() for nl in self.channels}

        # added KM 1/23/19
        for (nl, b) in self.buttons.items():
            b.name = nl
            b.clicked_signal.connect(self.handle_click)

        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        for i, nl in enumerate(sorted(self.channels, key=lambda nl: nl.split('@')[1])):
            if not i%16 and i != 0:
                self.layout.addWidget(Spacer(self.config))
            self.layout.addWidget(self.buttons[nl])
            self.buttons[nl].on_color = self.config.digital_colors[i%len(self.config.digital_colors)]
        self.layout.addWidget(QtGui.QWidget())
        self.setLayout(self.layout)

    def getLogic(self):
        return {nl: int(self.buttons[nl].is_checked) for nl in self.channels}

    def setLogic(self, sequence):
        for nameloc in self.channels:
            self.buttons[nameloc].setChecked(sequence[nameloc][self.position]['out'])

    # added KM 1/23/19
    def handle_click(self, nl):
        self.clicked_signal.emit(nl, self.position)

class DigitalArray(QtGui.QWidget):

    # added KM 1/23/19
    shift_toggled = False
    toggle_sign = False
    last_clicked = {'nl': '', 'position': 0}

    def __init__(self, channels, config):
        super(DigitalArray, self).__init__(None)
        self.channels = channels
        self.config = config
        self.populate()

        # added KM 1/23/19
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        for col in self.columns:
            col.clicked_signal.connect(self.handle_click)

        self.channel_to_index = {}
        self.index_to_channel = []
        for i, nl in enumerate(sorted(self.channels, key=lambda nl: nl.split('@')[1])):
            self.channel_to_index[nl] = i
            self.index_to_channel.append(nl)

    def populate(self):
        self.columns = [DigitalColumn(self.channels, self.config, i) for i in range(self.config.max_columns)]
        self.layout = QtGui.QHBoxLayout()
        for lc in self.columns:
            self.layout.addWidget(lc)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    def displaySequence(self, sequence): 
        shown_columns = sum([1 for c in self.columns if not c.isHidden()])
        num_to_show = len(sequence[self.config.timing_channel])
        if shown_columns > num_to_show:
            for c in self.columns[num_to_show: shown_columns][::-1]:
                c.hide()
        elif shown_columns < num_to_show:
            for c in self.columns[shown_columns:num_to_show]:
                c.show()
        for c in self.columns[:num_to_show]:
            c.setLogic(sequence)

    # added KM 1/23/19
    # watches for shift key depressed
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Shift:
            self.shift_toggled = True
        else:
            super(DigitalArray, self).keyPressEvent(event)

    # added KM 1/23/19
    # watches for shift key released
    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Shift:
            self.shift_toggled = False
        else:
            super(DigitalArray, self).keyPressEvent(event)

    # added KM 1/23/19
    # receives signals for clicks on the sequencer buttons
    # changes state of entire intermediate region when shift is depressed
    def handle_click(self, nl, position):
        nl = str(nl) # name loc of currently clicked channel
        last_nl = self.last_clicked['nl']
        last_position = self.last_clicked['position']

        # look for shift toggled
        if self.shift_toggled:
            # get indices
            last_index = self.channel_to_index[last_nl]
            current_index = self.channel_to_index[nl]
            
            # generate array of indices so we can grab every sequencer button
            # between the two that were clicked
            channel_index = range(min(last_index,current_index), max(last_index,current_index)+1)
            col_index = range(min(last_position, position), max(last_position, position) + 1)

            # flip the state of the two buttons that were most recently clicked
            # this is required to get a fair polling in the limit of few buttons being selected
            self.columns[last_position].buttons[last_nl].changeState()
            self.columns[position].buttons[last_nl].changeState()

            # take a poll to determine what sign to set the buttons to
            poll = 0
            for i in col_index:
                for j in channel_index:
                    # Checked counts as +1, unchecked as -1
                    if self.columns[i].buttons[self.index_to_channel[j]].is_checked:
                        poll += 1
                    else:
                        poll += -1

            # Set the state of all the buttons to the minority state
            if poll > 0:
                state = False
            else:
                state = True
            for i in col_index:
                for j in channel_index:
                    self.columns[i].buttons[self.index_to_channel[j]].setChecked(state)
        # Update what the last clicked button is
        self.last_clicked = {'nl': nl, 'position': position}

class NameBox(QtGui.QLabel):
    clicked = QtCore.pyqtSignal()
    def __init__(self, nameloc):
        super(NameBox, self).__init__(None)
        self.nameloc = nameloc
        name, loc = nameloc.split('@')
        self.setText(loc+': '+name)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter  )
        self.name = name
        self.off_color = '#ffffff'
        self.auto_color = '#dddddd'

    def mousePressEvent(self, x):
        self.clicked.emit()

    def displayModeState(self, x):
        if x['mode'] == 'manual':
            if x['manual_output']:
                self.setStyleSheet('QWidget {background-color: %s}' % self.on_color)
            else:
                self.setStyleSheet('QWidget {background-color: %s}' % self.off_color)
        else:
            self.setStyleSheet('QWidget {background-color: %s}' % self.auto_color)


class DigitalNameColumn(QtGui.QWidget):
    def __init__(self, channels, config):
        super(DigitalNameColumn, self).__init__(None)
        self.channels = channels
        self.config = config
        self.populate()

    def populate(self):
        self.labels = {nl: NameBox(nl) for nl in self.channels}
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(10, 0, 0, 0)
        for i, nl in enumerate(sorted(self.channels, key=lambda nl: nl.split('@')[1])):
            if not i%16 and i != 0:
                self.layout.addWidget(Spacer(self.config))
            self.layout.addWidget(self.labels[nl])
            self.labels[nl].on_color = self.config.digital_colors[i%len(self.config.digital_colors)]
        self.layout.addWidget(QtGui.QWidget())
        self.setLayout(self.layout)

class DigitalControl(QtGui.QWidget):
    def __init__(self, channels, config):
        super(DigitalControl, self).__init__(None)
        self.channels = channels
        self.config = config
        self.populate()

    def populate(self):
        self.nameColumn = DigitalNameColumn(self.channels, self.config)
        self.nameColumn.scrollArea = QtGui.QScrollArea()
        self.nameColumn.scrollArea.setWidget(self.nameColumn)
        self.nameColumn.scrollArea.setWidgetResizable(True)
        self.nameColumn.scrollArea.setHorizontalScrollBarPolicy(1)
        self.nameColumn.scrollArea.setVerticalScrollBarPolicy(1)
        self.nameColumn.scrollArea.setFrameShape(0)

        self.array = DigitalArray(self.channels, self.config)
        self.array.scrollArea = QtGui.QScrollArea()
        self.array.scrollArea.setWidget(self.array)
        self.array.scrollArea.setWidgetResizable(True)
        self.array.scrollArea.setHorizontalScrollBarPolicy(1)
        self.array.scrollArea.setVerticalScrollBarPolicy(1)
        self.array.scrollArea.setFrameShape(0)

        self.vscroll = QtGui.QScrollArea()
        self.vscroll.setWidget(QtGui.QWidget())
        self.vscroll.setHorizontalScrollBarPolicy(1)
        self.vscroll.setVerticalScrollBarPolicy(2)
        self.vscroll.setFrameShape(0)
        
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.nameColumn.scrollArea)
        self.layout.addWidget(self.array.scrollArea)
        self.layout.addWidget(self.vscroll)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.connectWidgets()
    
    def displaySequence(self, sequence):
        self.array.displaySequence(sequence)

    def updateParameters(self, parameter_values):
        pass
    
    def connectWidgets(self):
        self.vscrolls = [self.nameColumn.scrollArea.verticalScrollBar(),
                self.array.scrollArea.verticalScrollBar(),
                self.vscroll.verticalScrollBar()]
        for vs in self.vscrolls:
            vs.valueChanged.connect(self.adjust_for_vscroll(vs))

    def adjust_for_vscroll(self, scrolled):
        def afv():
            val = scrolled.value()
            for vs in self.vscrolls:
                vs.setValue(val)
        return afv

