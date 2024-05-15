from Titan.tint.visualization import full_domain
from Titan.tint import Cell_tracks
import os
import pyart
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal
from Config import DEFAULT_2D_TRACK_CONFIG
from Utils import listFile
from Radar import DataManager

class TrackThread(QObject):
    """
    Worker thread class.
    """
    # Define a signal to communicate with the main thread
    doneSignal = pyqtSignal()

    def __init__(self, params = None, DataManager = None):
        super().__init__()
        if params is None:
          self.params = DEFAULT_2D_TRACK_CONFIG
        else:
          self.params = params
        
        self.DataManager = DataManager
      
    def run(self):
      
      grids = (pyart.io.read_grid(fn) for fn in self.DataManager.grid_data)
      radar = pyart.io.read(self.DataManager.raw_data[0])

      tracks_obj = Cell_tracks()
      tracks_obj.get_tracks(grids)

      grids = (pyart.io.read_grid(fn) for fn in self.DataManager.grid_data)

      full_domain(tracks_obj, grids, "../Images/" + self.DataManager.radarName + self.DataManager.date + self.DataManager.mode, 
        lat_lines=np.arange(radar.latitude['data'][0]-2.0, radar.latitude['data'][0]+2.5, 0.5),
        lon_lines=np.arange(radar.longitude['data'][0]-2.0, radar.longitude['data'][0]+2.5, 0.5),
        tracers=True, vmin = int(self.params['VMIN']), vmax = int(self.params['VMAX']))
      self.doneSignal.emit()
