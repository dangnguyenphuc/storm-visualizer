import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pyart
import cartopy.crs as ccrs
import os

from Config import *

class App:

  # App States
  EXIT = 0
  THREE_DIM_SCREEN = 1

  def __init__(self):
    self.appState = App.THREE_DIM_SCREEN
    self.setUpPyGame()
    self.setUpTimer()

  def setUpPyGame(self):
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.set_mode((WINDOW_PROPERTIES.SCREEN_WIDTH, WINDOW_PROPERTIES.SCREEN_HEIGHT), pygame.OPENGL|pygame.DOUBLEBUF)

  def setUpOpenGL(self):
    glClearColor(0.0, 0.0, 0.0, 1)
    # glEnable(GL_DEPTH_TEST)

  def setUpTimer(self):
    self.clock = pygame.time.Clock()

  def update(self):
    # Rotate the cube
    # glRotatef(1, 0, 0, 1)  # Rotation angle and axis (x, y, z)
    pass


  def render(self):
    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw vertices
    # glBegin(GL_POINTS)
    # for vertex in vertices:
    #     glVertex3fv(vertex)
    # glEnd()

    # Update the display
    pygame.display.flip()



  def limitFrameRate(self):
    # Limit frame rate
    self.clock.tick(WINDOW_PROPERTIES.FPS)

  def run(self):
    while self.appState:
      self.eventHandler()

      self.update()
      self.render()
      self.limitFrameRate()

    self.destroy()

  def eventHandler(self):
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
          self.appState = App.EXIT

  def destroy(self):
    pygame.quit()