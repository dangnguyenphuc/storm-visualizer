import pygame
import numpy as np
import ctypes
import pyrr

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

class WINDOW_PROPERTIES:
  SCREEN_WIDTH = 800
  SCREEN_HEIGHT = 650

  FPS = 60

  VERTEX_SHADER_FILE = "shaders/vertex.txt"
  FRAGMENT_SHADER_FILE = "shaders/fragment.txt"

  EXAMPLE_TEXTURE_FILE = "assets/texture/Karina.jpg"

class WINDOW_STATE:
  EXIT = 0
  IS_RUNNING = 1

class Material:
  def __init__(self, filePath: str) -> None :
    image = pygame.image.load(filePath).convert_alpha()
    imageWidth, imageHeight = image.get_size()
    imageData = pygame.image.tostring(image, "RGBA")

    self.texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, self.texture)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, imageWidth, imageHeight, 0, GL_RGBA, GL_UNSIGNED_BYTE, imageData)
    glGenerateMipmap(GL_TEXTURE_2D)

  def use(self) -> None:
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, self.texture)

  def destroy(self) -> None:
    glDeleteTextures(1, (self.texture,))

class Cube:
    def __init__(self, position: list[float], eulers: list[float]) -> None:
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)

    def updateEulersY(self, value = 0.2):
      self.eulers[2] += value
      if(self.eulers[2] >= 360): self.eulers[2] = 360

    def updateEulersX(self, value = 0.2):
      self.eulers[0] += value
      if(self.eulers[0] >= 360): self.eulers[0] = 360

    def updateEulersZ(self, value = 0.2):
      self.eulers[1] += value
      if(self.eulers[1] >= 360): self.eulers[1] = 360

    def getModelTransform(self) -> np.ndarray:
        modelTranform = pyrr.matrix44.create_identity(dtype=np.float32)
        modelTranform = pyrr.matrix44.multiply(
          m1 = modelTranform,
          m2 = pyrr.matrix44.create_from_eulers(
            eulers = np.radians(self.eulers),
            dtype = np.float32
          )
        )

        return pyrr.matrix44.multiply(
          m1 = modelTranform,
          m2 = pyrr.matrix44.create_from_translation(
            vec=np.array(self.position),
            dtype=np.float32
          )
        )

class Mesh:
  def __init__(self) -> None :

    vertices = (
        -0.5, -0.5, -0.5, 0, 0,
        0.5, -0.5, -0.5, 1, 0,
        0.5,  0.5, -0.5, 1, 1,

        0.5,  0.5, -0.5, 1, 1,
        -0.5,  0.5, -0.5, 0, 1,
        -0.5, -0.5, -0.5, 0, 0,

        -0.5, -0.5,  0.5, 0, 0,
        0.5, -0.5,  0.5, 1, 0,
        0.5,  0.5,  0.5, 1, 1,

        0.5,  0.5,  0.5, 1, 1,
        -0.5,  0.5,  0.5, 0, 1,
        -0.5, -0.5,  0.5, 0, 0,

        -0.5,  0.5,  0.5, 1, 0,
        -0.5,  0.5, -0.5, 1, 1,
        -0.5, -0.5, -0.5, 0, 1,

        -0.5, -0.5, -0.5, 0, 1,
        -0.5, -0.5,  0.5, 0, 0,
        -0.5,  0.5,  0.5, 1, 0,

        0.5,  0.5,  0.5, 1, 0,
        0.5,  0.5, -0.5, 1, 1,
        0.5, -0.5, -0.5, 0, 1,

        0.5, -0.5, -0.5, 0, 1,
        0.5, -0.5,  0.5, 0, 0,
        0.5,  0.5,  0.5, 1, 0,

        -0.5, -0.5, -0.5, 0, 1,
        0.5, -0.5, -0.5, 1, 1,
        0.5, -0.5,  0.5, 1, 0,

        0.5, -0.5,  0.5, 1, 0,
        -0.5, -0.5,  0.5, 0, 0,
        -0.5, -0.5, -0.5, 0, 1,

        -0.5,  0.5, -0.5, 0, 1,
        0.5,  0.5, -0.5, 1, 1,
        0.5,  0.5,  0.5, 1, 0,

        0.5,  0.5,  0.5, 1, 0,
        -0.5,  0.5,  0.5, 0, 0,
        -0.5,  0.5, -0.5, 0, 1
    )
    self.vertexCount = len(vertices)//5
    self.vertices = np.array(vertices, dtype=np.float32)


    # vertex array object = buffer + attribute
    self.vao = glGenVertexArrays(1)
    glBindVertexArray(self.vao)
    self.vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
    glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5*ctypes.sizeof(ctypes.c_float), ctypes.c_void_p(0))

    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5*ctypes.sizeof(ctypes.c_float), ctypes.c_void_p( 0 + 3 * ctypes.sizeof(ctypes.c_float) ))

  def armForDrawing(self):
    glBindVertexArray(self.vao)

  def draw(self) -> None :
    glDrawArrays(GL_TRIANGLES, 0, self.vertexCount)

  def destroy(self) -> None :
    glDeleteVertexArrays(1, (self.vao,))
    glDeleteBuffers(1, (self.vbo,))

class App:
  def __init__(self) -> None :

    self.setupWindow()

    self.setupOpenGL()

    self.createAssets()

    self.setOnetimeUniforms()

    self.getUniformLocations()




  def setupWindow(self) -> None :
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.set_mode((WINDOW_PROPERTIES.SCREEN_WIDTH, WINDOW_PROPERTIES.SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)

    self.setupTimer()
    self.setupWindowState()

  def setupTimer(self) -> None :
    self.clock = pygame.time.Clock()

  def setupWindowState(self, state: int = WINDOW_STATE.IS_RUNNING):
    self.windowState = state

  def setupOpenGL(self) -> None :
    glClearColor(0.1, 0.2, 0.2, 1)
    # glEnable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

  def run(self) -> None :

    while self.windowState:

      for event in pygame.event.get():
        # if quit
        if event.type == pygame.QUIT:
          self.windowState = WINDOW_STATE.EXIT

      #update cube:
      self.cube.updateEulersX()
      self.cube.updateEulersY()

      # Clear screen and update
      glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
      glUseProgram(self.shader)




      glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, self.cube.getModelTransform())
      self.texture.use()
      self.cubeMesh.armForDrawing()
      self.cubeMesh.draw()

      pygame.display.flip()

      # set tick to 1/FPS
      self.clock.tick(WINDOW_PROPERTIES.FPS)

  def createShader(self, vertexFilePath: str, fragmentFilePath: str):

    with open(vertexFilePath, "r") as f:
      vertexSource = f.readlines()
    with open(fragmentFilePath, "r") as f:
      fragmentSource = f.readlines()

    shader = compileProgram(
      compileShader(vertexSource, GL_VERTEX_SHADER),
      compileShader(fragmentSource, GL_FRAGMENT_SHADER)
    )

    return shader

  def createAssets(self) -> None :
    self.cube = Cube(
      position = [0,0,-3],
      eulers = [0,0,0]
    )
    self.cubeMesh = Mesh()
    self.texture = Material(WINDOW_PROPERTIES.EXAMPLE_TEXTURE_FILE)
    self.shader = self.createShader(WINDOW_PROPERTIES.VERTEX_SHADER_FILE, WINDOW_PROPERTIES.FRAGMENT_SHADER_FILE)


  def setOnetimeUniforms(self):
    glUseProgram(self.shader)
    glUniform1i(glGetUniformLocation(self.shader, "imageTexture"), 0)

    projectionTransform = pyrr.matrix44.create_perspective_projection(
      fovy = 45, aspect = WINDOW_PROPERTIES.SCREEN_WIDTH/WINDOW_PROPERTIES.SCREEN_HEIGHT,
      near = 0.1, far=10, dtype=np.float32
    )

    glUniformMatrix4fv(
      glGetUniformLocation(self.shader, "projection"),
      1, GL_FALSE, projectionTransform
    )

  def getUniformLocations(self):
    glUseProgram(self.shader)
    self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")


  def quit(self) -> None :
    self.cubeMesh.destroy()
    self.texture.destroy()
    glDeleteProgram(self.shader)
    pygame.quit()

if __name__ == "__main__":
  app = App()
  app.run()
  app.quit()