import pygame
from pygame.locals import *

from Config import *
from Vertex import *
from Utils import create_shader, Timer
# from UI import *

class App:

  # App States
  EXIT = 0
  THREE_DIM_SCREEN = 1

  def __init__(self):

    self.appState = App.THREE_DIM_SCREEN

    self.setUpPyGame()

    self.setUpTimer()

    self.setUpOpenGL()

    self.createAsset()

    self.setOnetimeUniforms()

    self.getUniformLocations()

  def createAsset(self):
    self.entity = Entity(
                  position = [0,0,-20],
                  eulers = [0,-90,0]
                )

    self.vertex = VertexPoint()

    self.shader = create_shader(
                    vertex_filepath = "shaders/vertex.txt",
                    fragment_filepath = "shaders/fragment.txt"
                  )

  def setOnetimeUniforms(self) -> None:
    """
        Some shader data only needs to be set once.
    """

    glUseProgram(self.shader)

    # Use orthographic projection
    projection_transform = pyrr.matrix44.create_perspective_projection(
        fovy = 45, aspect = WINDOW_PROPERTIES.SCREEN_WIDTH/WINDOW_PROPERTIES.SCREEN_HEIGHT,
        near = 1.0, far = 20, dtype=np.float32
    )

    # assign projection_transform to SHADER SCRIPT
    glUniformMatrix4fv(
        glGetUniformLocation(self.shader,"projection"),
        1, GL_FALSE, projection_transform
    )

  def getUniformLocations(self) -> None:
    """
        Query and store the locations of shader uniforms
    """

    glUseProgram(self.shader)
    self.modelMatrixLocation = glGetUniformLocation(self.shader,"model")


  def setUpPyGame(self):
    """
        PyGame Initilization
    """
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.set_mode((WINDOW_PROPERTIES.SCREEN_WIDTH, WINDOW_PROPERTIES.SCREEN_HEIGHT), pygame.OPENGL|pygame.DOUBLEBUF)
    pygame.display.set_caption("RADAR 3D VISUALIZATION")


  def setUpOpenGL(self):
    """
        PyOpenGL default setups
    """
    glClearColor(0.0, 0.0, 0.0, 1)
    glEnable(GL_DEPTH_TEST)

  def setUpTimer(self):
    self.clock = pygame.time.Clock()
    self.switchFrameTimer = Timer(1)

  def update(self):
    """
    App update Logic
    """

    self.runTimers()

    # if self.switchFrameTimer.flag:
    #   self.vertex.update()
      # self.switchFrameTimer.reset()

  def runTimers(self):
    self.switchFrameTimer.run()

  def getModelTransform(self, index=1):
    """
    @param:
      + index: range(0,3)
        - 0: for x axis
        - 1: for y axis
        - 2: for z axis
    """
    self.entity.updateY()

    glUniformMatrix4fv(
        self.modelMatrixLocation, 1, GL_FALSE,
        self.entity.getModelTransform(index)
    )


  def render(self):
    """
    Draw all entities
    """

    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glUseProgram(self.shader)

    self.getModelTransform(1)

    self.vertex.arm()
    self.vertex.draw()

    # Update the display
    pygame.display.flip()

  def limitFrameRate(self):
    """
    Limit frame rate
    """

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
    self.vertex.clear()
    pygame.quit()