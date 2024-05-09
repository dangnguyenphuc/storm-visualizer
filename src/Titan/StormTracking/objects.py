import numpy as np
import pandas as pd
import pyart
from scipy import ndimage

def get_object_center(obj_id, labeled_image):
    """ Returns index of center pixel of the given object id from labeled
    image. The center is calculated as the median pixel of the object extent;
    it is not a true centroid. """
    obj_index = np.argwhere(labeled_image == obj_id)
    center = np.median(obj_index, axis=0).astype('i')
    return center

def get_obj_extent(labeled_image, obj_label):
    """ Takes in labeled image and finds the radius, area, and center of the
    given object. """
    obj_index = np.argwhere(labeled_image == obj_label)

    zlength = np.max(obj_index[:, 0]) - np.min(obj_index[:, 0]) + 1
    ylength = np.max(obj_index[:, 1]) - np.min(obj_index[:, 1]) + 1
    xlength = np.max(obj_index[:, 2]) - np.min(obj_index[:, 2]) + 1
    obj_radius = np.max((xlength, ylength, zlength))/2
    obj_center = np.round(np.median(obj_index, axis=0), 0)
    obj_volume = len(obj_index[:, 0])

    obj_extent = {'obj_center': obj_center, 'obj_radius': obj_radius,
                  'obj_volume': obj_volume, 'obj_index': obj_index}
    return obj_extent


