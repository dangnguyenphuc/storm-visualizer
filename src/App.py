import pygame
from pygame.locals import *

from Config import *
from Vertex import *
from Utils import *
# from UI import *

class App:

  # App States
  EXIT = 0
  THREE_DIM_SCREEN = 1

  def __init__(self):
    self.appState = App.THREE_DIM_SCREEN
    self.setUpPyGame()
    self.setUpTimer()
    self.setUpVertices()

  def setUpVertices(self):
    self.vertex = VertexPoint()

  def setUpPyGame(self):
    pygame.init()
    pygame.display.set_mode((WINDOW_PROPERTIES.SCREEN_WIDTH, WINDOW_PROPERTIES.SCREEN_HEIGHT), pygame.OPENGL|pygame.DOUBLEBUF)

  def setUpOpenGL(self):
    # Set up the OpenGL perspective
    gluPerspective(0, (WINDOW_PROPERTIES.SCREEN_WIDTH / WINDOW_PROPERTIES.SCREEN_HEIGHT), 0.1, 50.0)

    # Move "camera" back a bit
    glTranslatef(0.0, 0.0, -5.0)
    glClearColor(0.0, 0.0, 0.0, 1)
    # glRotatef(-90, 1, 0, 0)  # Rotation angle and axis (x, y, z)

  def setUpTimer(self):
    self.clock = pygame.time.Clock()
    self.switchFrameTimer = Timer(1)

  def update(self):
    # Rotate
    glRotatef(1, 0, 1, 0)  # Rotation angle and axis (x, y, z)

    self.runTimers()

    if self.switchFrameTimer.flag:
      self.vertex.update()
      self.switchFrameTimer.reset()

  def runTimers(self):
    self.switchFrameTimer.run()

  def render(self):
    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw vertices
    self.vertex.draw()

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