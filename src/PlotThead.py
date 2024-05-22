from PyQt5.QtCore import QObject, pyqtSignal
from Radar import Radar

class PlotThread(QObject):
    doneSignal = pyqtSignal()

    def __init__(self, Radar: Radar = None):
        super().__init__()
        self.radar = Radar
      
    def plot(self):
      self.radar.plot()
      self.doneSignal.emit()
