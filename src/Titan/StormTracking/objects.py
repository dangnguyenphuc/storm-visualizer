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

def init_current_objects(first_frame, second_frame, pairs, counter):
    """ Returns a dictionary for objects with unique ids and their
    corresponding ids in frame1 and frame1. This function is called when
    echoes are detected after a period of no echoes. """
    nobj = np.max(first_frame)

    id1 = np.arange(nobj) + 1
    uid = counter.next_uid(count=nobj)
    id2 = pairs
    obs_num = np.zeros(nobj, dtype='i')
    origin = np.array(['-1']*nobj)

    current_objects = {'id1': id1, 'uid': uid, 'id2': id2,
                       'obs_num': obs_num, 'origin': origin}
    current_objects = attach_last_heads(first_frame, second_frame,
                                        current_objects)
    return current_objects, counter

def update_current_objects(frame1, frame2, pairs, old_objects, counter):
    """ Removes dead objects, updates living objects, and assigns new uids to
    new-born objects. """
    nobj = np.max(frame1)
    id1 = np.arange(nobj) + 1
    uid = np.array([], dtype='str')
    obs_num = np.array([], dtype='i')
    origin = np.array([], dtype='str')

    for obj in np.arange(nobj) + 1:
        if obj in old_objects['id2']:
            obj_index = old_objects['id2'] == obj
            uid = np.append(uid, old_objects['uid'][obj_index])
            obs_num = np.append(obs_num, old_objects['obs_num'][obj_index] + 1)
            origin = np.append(origin, old_objects['origin'][obj_index])
        else:
            #  obj_orig = get_origin_uid(obj, frame1, old_objects)
            obj_orig = '-1'
            origin = np.append(origin, obj_orig)
            if obj_orig != '-1':
                uid = np.append(uid, counter.next_cid(obj_orig))
            else:
                uid = np.append(uid, counter.next_uid())
            obs_num = np.append(obs_num, 0)
    id2 = pairs
    current_objects = {'id1': id1, 'uid': uid, 'id2': id2,
                       'obs_num': obs_num, 'origin': origin}
    current_objects = attach_last_heads(frame1, frame2, current_objects)
    return current_objects, counter

def attach_last_heads(frame1, frame2, current_objects):
    """ Attaches last heading information to current_objects dictionary. """
    nobj = len(current_objects['uid'])
    heads = np.ma.empty((nobj, 3))
    for obj in range(nobj):
        if ((current_objects['id1'][obj] > 0) and
                (current_objects['id2'][obj] > 0)):
            center1 = get_object_center(current_objects['id1'][obj], frame1)
            center2 = get_object_center(current_objects['id2'][obj], frame2)
            heads[obj, :] = center2 - center1
        else:
            heads[obj, :] = np.ma.array([-999, -999], mask=[True, True])

    current_objects['last_heads'] = heads
    return current_objects
