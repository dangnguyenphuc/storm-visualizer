from Radar import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from sklearn.preprocessing import MinMaxScaler
import numpy as np

from functools import partial
import multiprocessing

class VertexPoint:
  def __init__(self, index = 0, threshold = 0):
    self.setUpRadar(index=index)
    self.getVertices(threshold)

  def setUpRadar(self, index = 0,filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str = DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    self.radar = Radar(index, filePath, radarName, date, mode)

  def getVertices(self, threshold = 0):
    self.vertices = self.get_all_vertices_by_threshold(threshold)

  def update(self, threshold = 0):
    self.radar.update()
    self.getVertices(threshold)

  def draw(self):
    # Draw the vertices (points)
    glBegin(GL_POINTS)
    for vertex in self.vertices:
      glVertex3fv(vertex)
    glEnd()

  def clear(self):
    self.radar = None
    self.vertices = []

  def get_gate_set(self, sweep_num):
    gates = self.radar.data.get_gate_x_y_z(sweep_num)

    gate_set = []
    for i in range(len(gates[0])):
        for j in range(len(gates[0][i])):
            gate_set += [
                    [
                        gates[0][i][j],     #   X
                        gates[1][i][j],     #   Y
                        gates[2][i][j]      #   Z
                    ]
                ]
    gate_set = np.array(gate_set)
    return gate_set

  def get_gate_reflectivity(self, sweep_num):
    start_ray_index = self.radar.data.sweep_start_ray_index['data'][sweep_num]
    end_ray_index = self.radar.data.sweep_end_ray_index['data'][sweep_num]

    return self.radar.data.fields['reflectivity']['data'][start_ray_index : end_ray_index+1].flatten()

  def get_vertices_by_threshold(self, threshold = 0, sweep = 0):
    print("running sweep", sweep)
    sweep_gate_position = self.get_gate_set(sweep)

    # scale
    scaler = MinMaxScaler(feature_range=(-1.0, 1.0))
    sweep_gate_position = scaler.fit_transform(sweep_gate_position)

    sweep_gate_reflectivies = self.get_gate_reflectivity(sweep)
    vertices = []
    for i in range(len(sweep_gate_reflectivies)):
      if sweep_gate_reflectivies[i] >= threshold:
        vertices.append(sweep_gate_position[i][0])
        vertices.append(sweep_gate_position[i][1])
        vertices.append(sweep_gate_position[i][2])
    return vertices

  def get_all_vertices_by_threshold(self, threshold = 0):
    # Create a pool of processes (adjust num_processes as needed)
    with multiprocessing.Pool(processes=self.radar.data.nsweeps) as pool:
      # Calculate squares in parallel and collect results
      vertices = pool.starmap(
        self.get_vertices_by_threshold,                           # function
        [(threshold, i) for i in range(self.radar.data.nsweeps)]  # arguments
      )
      pool.close()

    return vertices
