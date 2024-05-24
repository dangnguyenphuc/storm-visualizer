import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import pyart
from scipy import ndimage
import pandas as pd
import numpy as np
from StormTracking.grid_utils import *
from sklearn.preprocessing import MinMaxScaler
import pickle

params = {'FIELD_THRESH': 32,
 'MIN_SIZE': 1,
 'SEARCH_MARGIN': 4000,
 'FLOW_MARGIN': 10000,
 'MAX_FLOW_MAG': 50,
 'MAX_DISPARITY': 999,
 'MAX_SHIFT_DISP': 15,
 'ISO_THRESH': 8,
 'ISO_SMOOTH': 3}

grid = pyart.io.read_grid("/Users/phucdang/Documents/dangnguyen/Document/project/titan/Data/NHB/2023/06/01/grid/1_prt/grid_NHB230601055008.nc")

def getSizeTable(frame):
  flat_image = pd.Series(frame.flatten())
  flat_image = flat_image[flat_image > 0]
  size_table = flat_image.value_counts(sort=False)
  return size_table

def getZIndices(array, value):
    z_indices, _, _ = np.where(array == value)
    unique_z_indices = np.unique(z_indices)
    if len(unique_z_indices) == 0:
        return None
    else:
        return unique_z_indices
        
def getEdgeIndices(image):
  borders = np.logical_xor(image, ndimage.binary_erosion(image))
  edge_indices = np.transpose(np.nonzero(borders))
  return edge_indices



raw, frame = extract_grid_data(grid, "reflectivity", get_grid_size(grid), params)
print(np.unique(frame))

z = getZIndices(frame, 1)

edge_points = []
l = []
start = 0
for val in z:
  edge_indices = getEdgeIndices(frame[val])
  points = np.vstack((
    grid.x['data'][edge_indices[:, 0]], 
    grid.y['data'][edge_indices[:, 1]]
    )).T
  points = np.hstack((points, np.full((points.shape[0], 1), grid.z['data'][val])))
  edge_points.append(points)
  end = start + len(points)
  l.append([start, end])
  start = end
scaler = MinMaxScaler(feature_range=(-2.5, 2.5))
# Concatenate all arrays into a single 2D array
concatenated_array = np.concatenate(edge_points, axis=0)
scaled_array = scaler.fit_transform(concatenated_array)
edge_points = []
for i in l:
  edge_points.append(scaled_array[i[0]:i[1]])

z = getZIndices(frame, 2)

edge_points2 = []
l = []
start = 0
for val in z:
  edge_indices = getEdgeIndices(frame[val])
  points = np.vstack((
    grid.x['data'][edge_indices[:, 0]], 
    grid.y['data'][edge_indices[:, 1]]
    )).T
  points = np.hstack((points, np.full((points.shape[0], 1), grid.z['data'][val])))
  edge_points2.append(points)
  end = start + len(points)
  l.append([start, end])
  start = end
scaler = MinMaxScaler(feature_range=(-2.5, 2.5))
# Concatenate all arrays into a single 2D array
concatenated_array = np.concatenate(edge_points2, axis=0)
scaled_array = scaler.fit_transform(concatenated_array)
edge_points2 = []
for i in l:
  edge_points2.append(scaled_array[i[0]:i[1]])

def draw_object(edge_points):

    num_planes = len(edge_points)
    side_planes = []
    side_planes_it = num_planes

    for i in range(side_planes_it - 1):
      points = np.concatenate((edge_points[i], edge_points[i+1]), axis = 0)
      side_planes.append(points)

    for i in range(len(side_planes)):
      glBegin(GL_LINES)
      for j in range(len(side_planes[i])):
          for k in range(i + 1, len(side_planes[i])):
              glVertex3fv(side_planes[i][j])
              glVertex3fv(side_planes[i][k])
      glEnd()
    
    for i in range(num_planes):
        glBegin(GL_POLYGON)
        for point in edge_points[i]:
            glVertex3fv(point)
        glEnd() 
    
def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -10)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        glRotatef(1, 1, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glColor3f(1.0, 1.0, 1.0)
        draw_object(edge_points)
        glColor3f(1.0, 0.0, 0.0)
        draw_object(edge_points2)
        pygame.display.flip()
        pygame.time.wait(1)

if __name__ == "__main__":
    main()