from tint.visualization import full_domain
from tint import Cell_tracks
import os
import pyart
import numpy as np
from scipy import ndimage 

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

########################################################################### 2D
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
########################################################################### 2D


def fft_flowvectors(im1, im2, global_shift=False):
    """ Estimates flow vectors in two images using cross covariance. """
    if not global_shift and (np.max(im1) == 0 or np.max(im2) == 0):
        return None

    crosscov = fft_crosscov(im1, im2)
    sigma = (1/8) * min(crosscov.shape)
    cov_smooth = ndimage.filters.gaussian_filter(crosscov, sigma)
    dims = np.array(im1.shape)

    pshift = np.argwhere(cov_smooth == np.max(cov_smooth))[0]
    
    rs = np.ceil(dims[0]/2).astype('int')
    cs = np.ceil(dims[1]/2).astype('int')
    ls = np.ceil(dims[2]/2).astype('int')
    # Calculate shift relative to center - see fft_shift.
    pshift = pshift - (dims - [rs, cs, ls])
    return pshift


def fft_crosscov(im1, im2):
    """ Computes cross correlation matrix using FFT method. """
    fft1_conj = np.conj(np.fft.fftn(im1))
    fft2 = np.fft.fftn(im2)
    normalize = abs(fft2*fft1_conj)
    normalize[normalize == 0] = 1  # prevent divide by zero error
    cross_power_spectrum = (fft2*fft1_conj)/normalize
    crosscov = np.fft.ifftn(cross_power_spectrum)
    crosscov = np.real(crosscov)
    return np.fft.fftshift(crosscov)


def fft_shift(fft_mat):
    """ Rearranges the cross correlation matrix so that 'zero' frequency or DC
    component is in the middle of the matrix. Taken from stackoverflow Que.
    30630632. """
    if type(fft_mat) is np.ndarray:
        rs = np.ceil(fft_mat.shape[0]/2).astype('int')
        cs = np.ceil(fft_mat.shape[1]/2).astype('int')
        quad1 = fft_mat[:rs, :cs]
        quad2 = fft_mat[:rs, cs:]
        quad3 = fft_mat[rs:, cs:]
        quad4 = fft_mat[rs:, :cs]
        centered_t = np.concatenate((quad4, quad1), axis=0)
        centered_b = np.concatenate((quad3, quad2), axis=0)
        centered = np.concatenate((centered_b, centered_t), axis=1)
        # Thus centered is formed by shifting the entries of fft_mat
        # up/left by [rs, cs] indices, or equivalently down/right by
        # (fft_mat.shape - [rs, cs]) indices, with edges wrapping. 
        return centered
    else:
        print('input to fft_shift() should be a matrix')
        return


def get_global_shift(im1, im2, params):
    """ Returns standardazied global shift vector. im1 and im2 are full frames
    of raw DBZ values. """
    if im2 is None:
        return None
    shift = fft_flowvectors(im1, im2, global_shift=True)
    return shift

grid1 = pyart.io.read_grid("/Users/phucdang/Documents/dangnguyen/Document/project/titan/Data/NHB/2023/06/05/grid/1_prt/grid_NHB230605000007.nc")
grid2 = pyart.io.read_grid("/Users/phucdang/Documents/dangnguyen/Document/project/titan/Data/NHB/2023/06/05/grid/1_prt/grid_NHB230605001008.nc")

masked1 = grid1.fields["reflectivity"]["data"]
masked1.data[masked1.data == masked1.fill_value] = 0
masked2 = grid2.fields["reflectivity"]["data"]
masked2.data[masked2.data == masked2.fill_value] = 0

raw1 = masked1.data
raw2 = masked2.data

print(get_global_shift(raw1,raw2,None))


