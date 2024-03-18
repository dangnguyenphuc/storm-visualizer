from Radar import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from sklearn.preprocessing import MinMaxScaler
import numpy as np

# from functools import partial
# import concurrent.futures

class VertexPoint:
  def __init__(self, index = 0, threshold = 0):
    self.setUpRadar(index=index)
    self.setUpThreshold(threshold)
    self.getVertices()

  def setUpRadar(self, index = 0,filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str = DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    self.radar = Radar(index, filePath, radarName, date, mode)

  def setUpThreshold(self, threshold = 0):
    self.threshold = threshold

  def getVertices(self):
    self.vertices = self.get_all_vertices_by_threshold()
    # print("Nums to render:", len(self.vertices))

  def update(self):
    self.radar.update()
    self.getVertices()

  def draw(self):
    # Draw the vertices (points)
    glBegin(GL_POINTS)
    for vertex in self.vertices:
      glVertex3fv(vertex)
    glEnd()

  def clear(self):
    self.radar = None
    self.vertices = []

  def get_gate_reflectivity(self, sweep_num):
    start_ray_index = self.radar.data.sweep_start_ray_index['data'][sweep_num]
    end_ray_index = self.radar.data.sweep_end_ray_index['data'][sweep_num]

    return self.radar.data.fields['reflectivity']['data'][start_ray_index : end_ray_index+1].flatten()

  def get_vertices_positionX(self, indices=None):
    if indices:
      return self.radar.data.gate_x["data"][indices]
    else:  return self.radar.data.gate_x["data"]

  def get_vertices_positionY(self, indices=None):
    if indices:
      return self.radar.data.gate_y["data"][indices]
    else:  return self.radar.data.gate_y["data"]

  def get_vertices_positionZ(self, indices=None):
    if indices:
      return self.radar.data.gate_z["data"][indices]
    else:  return self.radar.data.gate_z["data"]

  def get_vertices_position(self, scaler):
    return scaler.fit_transform(
      np.column_stack(
        (
          self.radar.data.gate_x["data"].flatten(),
          self.radar.data.gate_y["data"].flatten(),
          self.radar.data.gate_z["data"].flatten()
        )
      )
    )

  def get_all_vertices_by_threshold(self):
    # all_vertices = []
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     # Use ThreadPoolExecutor.map for simplified management
    #     nsweeps = self.radar.data.nsweeps
    #     futures = executor.map(self.get_vertices_by_threshold, range(nsweeps))

    #     # Iterate through results
    #     for result in futures:
    #         all_vertices.extend(result)

    # return all_vertices
    reflectivity = self.radar.data.fields['reflectivity']['data'].flatten()

    indices = np.where(np.logical_and(np.logical_not(reflectivity.mask), reflectivity.data >= self.threshold))
    scaler = MinMaxScaler(feature_range=(-1.0, 1.0))
    vertices = self.get_vertices_position(scaler)
    return vertices[indices].flatten()
