from tint.visualization import full_domain
from tint import Cell_tracks
import os
import pyart
import numpy as np

"""
Các thông số để gen TRACK:

{'FIELD_THRESH': 32,
 'MIN_SIZE': 8,
 'SEARCH_MARGIN': 4000,
 'FLOW_MARGIN': 10000,
 'MAX_FLOW_MAG': 50,
 'MAX_DISPARITY': 999,
 'MAX_SHIFT_DISP': 15,
 'ISO_THRESH': 8,
 'ISO_SMOOTH': 3,
 'GS_ALT': 1500}

Đồng thời sau đây là một số thông số người dùng có thể tự định nghĩa để họ được hình ảnh mong muốn:
vmin = 0
vmax = 0
"""

PATH = "../Data/NHB/2023/06/01/"
filenames = [PATH + "grid/1_prt/" + f for f in os.listdir(PATH+ "grid/1_prt/") if f != ".DS_Store"]
filenames.sort()
grids = (pyart.io.read_grid(fn) for fn in filenames)

tracks_obj = Cell_tracks()
tracks_obj.params['MIN_SIZE'] = 10
tracks_obj.get_tracks(grids)



grids = (pyart.io.read_grid(fn) for fn in filenames)
radar = pyart.io.read("../Data/NHB/2023/06/01/2_prt/NHB230601000304.RAWLGZZ")

full_domain(tracks_obj, grids, "../Images/NHB/2023/06/01/1_prt/", 
        lat_lines=np.arange(radar.latitude['data'][0]-2.0, radar.latitude['data'][0]+2.5, 0.5),
        lon_lines=np.arange(radar.longitude['data'][0]-2.0, radar.longitude['data'][0]+2.5, 0.5),
        tracers=True, vmin = 0)



