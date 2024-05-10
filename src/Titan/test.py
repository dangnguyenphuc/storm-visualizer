from tint.visualization import full_domain
from tint import Cell_tracks
import os
import pyart
import numpy as np
from scipy import ndimage 

################################# 2D
# PATH = "../Data/NHB/2023/06/01/"
# filenames = [PATH + "grid/1_prt/" + f for f in os.listdir(PATH+ "grid/1_prt/") if f != ".DS_Store"]
# filenames.sort()
# grids = (pyart.io.read_grid(fn) for fn in filenames)

# tracks_obj = Cell_tracks()
# tracks_obj.params['MIN_SIZE'] = 10
# tracks_obj.get_tracks(grids)



# grids = (pyart.io.read_grid(fn) for fn in filenames)
# radar = pyart.io.read("../Data/NHB/2023/06/01/2_prt/NHB230601000304.RAWLGZZ")

# full_domain(tracks_obj, grids, "../Images/NHB/2023/06/01/1_prt/", 
#         lat_lines=np.arange(radar.latitude['data'][0]-2.0, radar.latitude['data'][0]+2.5, 0.5),
#         lon_lines=np.arange(radar.longitude['data'][0]-2.0, radar.longitude['data'][0]+2.5, 0.5),
#         tracers=True, vmin = 0)
################################# 2D



from StormTracking.phase_correlation import get_global_shift
from StormTracking.objects import get_object_center
import pyart


###################### FFT_FLOWVECTOR
# grid1 = pyart.io.read_grid("/Users/phucdang/Documents/dangnguyen/Document/project/titan/Data/NHB/2023/06/05/grid/1_prt/grid_NHB230605000007.nc")
# grid2 = pyart.io.read_grid("/Users/phucdang/Documents/dangnguyen/Document/project/titan/Data/NHB/2023/06/05/grid/1_prt/grid_NHB230605001008.nc")

# masked1 = grid1.fields["reflectivity"]["data"]
# masked1.data[masked1.data == masked1.fill_value] = 0
# masked2 = grid2.fields["reflectivity"]["data"]
# masked2.data[masked2.data == masked2.fill_value] = 0

# raw1 = masked1.data
# raw2 = masked2.data

# print(get_global_shift(raw1,raw2,None))
###################### FFT_FLOWVECTOR



############### OBJECT CENTER
# labeled_image = np.zeros((5, 5, 5), dtype=int)
# labeled_image[2:5, 2:5, 1:4] = 1  # Assign object ID 1 to a cube in the center

# # Calculate the center of the object
# center = get_object_center(1, labeled_image)

# print(labeled_image, center)
############### OBJECT CENTER


# labeled_image = np.zeros((5, 5, 5), dtype=int)
# labeled_image[2:5, 2:5, 1:4] = 1  # Assign object ID 1 to a cube in the center
# print(np.argwhere(labeled_image == 1))

# print(labeled_image)

from StormTracking.grid_utils import get_grid_size

# grid1 = pyart.io.read_grid("/Users/phucdang/Documents/dangnguyen/Document/project/titan/Data/NHB/2023/06/05/grid/1_prt/grid_NHB230605000007.nc")
# print(get_grid_size(grid1))

dims = (4,4,4)
data = np.arange(np.prod(dims)).reshape(dims)

max_proj = np.max(data, axis=0)
# smooth = ndimage.filters.gaussian_filter(max_proj, 3)
padded = np.pad(max_proj, 1, mode='constant')
print(padded)




