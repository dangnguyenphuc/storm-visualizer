import numpy as np
from scipy import ndimage

def get_ambient_flow(obj_extent, img1, img2, params, grid_size):
    """ Takes in object extent and two images and returns ambient flow. Margin
    is the additional region around the object used to compute the flow
    vectors. """
    margin_z = params['FLOW_MARGIN'] / grid_size[0]
    margin_y = params['FLOW_MARGIN'] / grid_size[1]
    margin_x = params['FLOW_MARGIN'] / grid_size[2]

    z_lb = obj_extent['obj_center'][0] - obj_extent['obj_radius'] - margin_z
    z_ub = obj_extent['obj_center'][0] + obj_extent['obj_radius'] + margin_z
    y_lb = obj_extent['obj_center'][1] - obj_extent['obj_radius'] - margin_y
    y_ub = obj_extent['obj_center'][1] + obj_extent['obj_radius'] + margin_y
    x_lb = obj_extent['obj_center'][2] - obj_extent['obj_radius'] - margin_x
    x_ub = obj_extent['obj_center'][2] + obj_extent['obj_radius'] + margin_x
    z_lb = int(z_lb)
    z_ub = int(z_ub)
    y_lb = int(y_lb)
    y_ub = int(y_ub)
    x_lb = int(x_lb)
    x_ub = int(x_ub)

    dims = img1.shape

    z_lb = np.max([z_lb, 0])
    z_ub = np.min([z_ub, dims[0]])
    y_lb = np.max([y_lb, 0])
    y_ub = np.max([y_ub, dims[1]])
    x_lb = np.max([x_lb, 0])
    x_ub = np.max([x_ub, dims[2]])

    flow_region1 = np.copy(img1[z_lb:z_ub+1, y_lb:y_ub+1, x_lb:x_ub+1])
    flow_region2 = np.copy(img2[z_lb:z_ub+1, y_lb:y_ub+1, x_lb:x_ub+1])

    flow_region1[flow_region1 != 0] = 1
    flow_region2[flow_region2 != 0] = 1
    return fft_flowvectors(flow_region1, flow_region2)

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
