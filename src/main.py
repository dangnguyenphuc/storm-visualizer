import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import pyart
import cartopy.crs as ccrs
import os


def get_gate_set(sweep_num, radar):
    gates = radar.get_gate_x_y_z(sweep_num)

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

def get_gate_reflectivity(sweep_num, radar):
    start_ray_index = radar.sweep_start_ray_index['data'][sweep_num]
    end_ray_index = radar.sweep_end_ray_index['data'][sweep_num]

    return radar.fields['reflectivity']['data'][start_ray_index : end_ray_index+1].flatten()

def get_vertices_by_threshold(radar, threshold = 30, sweep = 3):
  sweep_gate_position = get_gate_set(sweep, radar)

  # scale
  scaler = MinMaxScaler(feature_range=(-1, 1))
  sweep_gate_position = scaler.fit_transform(sweep_gate_position)

  sweep_gate_reflectivies = get_gate_reflectivity(sweep, radar)
  vertices = []
  for i in range(len(sweep_gate_reflectivies)):
    if sweep_gate_reflectivies[i] >= threshold:
      vertices.append((sweep_gate_position[i][0], sweep_gate_position[i][1], sweep_gate_position[i][2]))
  return vertices


day = '01/'
path = '../Data/'
data = [path + day + fileName for fileName in os.listdir(path + day)]
data.sort()
firstDir = path + day + '1_prt/'
secondDir = path + day + '2_prt/'
one_prt = [firstDir + fileName for fileName in os.listdir(firstDir)]
two_prt = [secondDir + fileName for fileName in os.listdir(secondDir)]

radar = pyart.io.read(one_prt[0])
vertices = get_vertices_by_threshold(radar)

# print(vertices)

# Initialize Pygame
pygame.init()

# Create a Pygame window
display = (800, 600)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

# Set up the OpenGL perspective
gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)

# Move "camera" back a bit
glTranslatef(0.0, 0.0, -5)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Rotate the cube
    glRotatef(1, 0, 1, 0)  # Rotation angle and axis (x, y, z)

    # Draw the vertices (points)
    glBegin(GL_POINTS)
    for vertex in vertices:
        glVertex3fv(vertex)
    glEnd()

    # Update the display
    pygame.display.flip()

    # Limit frame rate
    pygame.time.wait(10)

pygame.quit()
