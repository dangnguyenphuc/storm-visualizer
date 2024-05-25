from PyQt5.QtCore import QObject, pyqtSignal
from Radar import Radar

class PlotWorker(QObject):
    doneSignal = pyqtSignal()

    def __init__(self, Radar: Radar = None):
        super().__init__()
        self.radar = Radar
        self.mode = None
        self.sweep = None
      
    def plot(self):
        self.radar.plot(mode=self.mode, sweep=self.sweep)
        self.doneSignal.emit()