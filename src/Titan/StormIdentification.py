from scipy import ndimage
import pandas as pd
import numpy as np
import copy

# get storms size
def getSizeTable(frame):
  flat_image = pd.Series(frame.flatten())
  flat_image = flat_image[flat_image > 0]
  size_table = flat_image.value_counts(sort=False)
  return size_table

# get Z indices of a storm
def getZIndices(array, value):
    z_indices, _, _ = np.where(array == value)
    unique_z_indices = np.unique(z_indices)
    if len(unique_z_indices) == 0:
        return None
    else:
        return unique_z_indices

# get Edge points indices 
def getEdgeIndices(image):
  borders = np.logical_xor(image, ndimage.binary_erosion(image))
  edge_indices = np.transpose(np.nonzero(borders))
  return edge_indices

def getStorm(grid, threshold, minSize):
  masked = grid.fields['reflectivity']['data']
  masked.data[masked.data == masked.fill_value] = 0
  masked.data[masked.data < threshold] = 0

  frame, count = ndimage.label(masked.data)
  size_table = getSizeTable(frame)
  small_objects = size_table.keys()[size_table < minSize]
  for obj in small_objects:
    frame[frame == obj] = 0

  # reset storm indices number after removing invalid storm which is small
  frame, count = ndimage.label(frame)
  return (frame, count)

def getStormCount(frame):
  return np.max(frame)

# index: Start from 1
def getStormWithIndex(grid, frame, index=1):
  storm = copy.deepcopy(frame)
  storm[storm != index] = 0
  z = getZIndices(storm, index)

  edge_points = []
  plane = []  # ref to a plane with start and end point index
  start = 0

  for val in z:
    edge_indices = getEdgeIndices(frame[val])
    points = np.vstack((
      grid.y['data'].data[edge_indices[:, 1]],
      grid.x['data'].data[edge_indices[:, 0]]
      )).T
    points = np.hstack((points, np.full((points.shape[0], 1), grid.z['data'][val])))
    edge_points.append(points)
    end = start + len(points)
    plane.append([start, end])
    start = end

  edge_points_positions = np.concatenate(edge_points, axis=0)
  return edge_points_positions, plane
