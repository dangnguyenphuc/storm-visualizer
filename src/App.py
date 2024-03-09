import pygame
from pygame.locals import *


class WINDOW_PROPERTIES:
  WINDOW_WIDTH = 1000
  WINDOW_HEIGHT = 800

class App:

  # App States
  EXIT = 0
  THREE_DIM_SCREEN = 1

  def __init__(self):
    self.clock = pygame.time.Clock()
    pass

  def update(self):
    pass

  def render(self):
    pass

  def run(self):
    pass
