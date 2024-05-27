import os
import pyart
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal
from Config import DEFAULT_GRID_CONFIG
from Radar import DataManager

class GenGridThread(QObject):
    """
    Worker thread class.
    """
    # Define a signal to communicate with the main thread
    doneSignal = pyqtSignal()

    def __init__(self, params = None, DataManager = None):
        super().__init__()
        if params is None:
          self.params = DEFAULT_GRID_CONFIG
        else:
          self.params = params
        
        self.DataManager = DataManager
      
    def run(self):
      self.DataManager.genGrid(self.params)
      self.doneSignal.emit()
