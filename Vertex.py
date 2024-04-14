from Radar import *

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileProgram,compileShader
import pyrr
from sklearn.preprocessing import MinMaxScaler
import numpy as np

class Entity:
    """
        A basic object in the world, with a position and rotation.
    """

    def __init__(self, position: list[float], eulers: list[float]):
        """
            Initialize the entity.

            Parameters:

                position: the position of the entity.

                eulers: the rotation of the entity
                        about each axis.
        """

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)

    def updateY(self) -> None:
        """
            Update the object, this is hard coded for now.
        """

        self.eulers[1] += 0.25

        if self.eulers[1] > 360:
            self.eulers[1] -= 360

    def updateX(self) -> None:
        """
            Update the object, this is hard coded for now.
        """

        self.eulers[0] += 0.25

        if self.eulers[0] > 360:
            self.eulers[0] -= 360

    def updateZ(self) -> None:
        """
            Update the object, this is hard coded for now.
        """

        self.eulers[2] += 0.25

        if self.eulers[2] > 360:
            self.eulers[2] -= 360

    def getModelTransform(self, index = 1) -> np.ndarray:
        """
            Returns the entity's model to world
            transformation matrix.
        """

        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)

        # axis = [0,0,0]
        # axis[index] = 1
        # model_transform = pyrr.matrix44.multiply(
        #     m1=model_transform,
        #     m2=pyrr.matrix44.create_from_axis_rotation(
        #         axis = axis,
        #         theta = np.radians(self.eulers[1]),
        #         dtype = np.float32
        #     )
        # )

        # Rotate around Y-axis by -90 degrees (or 270 degrees)
        if index == 1:
            model_transform = pyrr.matrix44.multiply(
                m1=model_transform,
                m2=pyrr.matrix44.create_from_axis_rotation(
                    axis=[1, 0, 0],  # X-axis
                    theta=np.radians(-90),  # Rotate -90 degrees around Y-axis
                    dtype=np.float32
                )
            )

        # Rotate around X-axis
        model_transform = pyrr.matrix44.multiply(
            m1=model_transform,
            m2=pyrr.matrix44.create_from_axis_rotation(
                axis=[0, 1, 0],  # X-axis
                theta=np.radians(self.eulers[1]),  # Rotate around X-axis based on entity's rotation
                dtype=np.float32
            )
        )

        return pyrr.matrix44.multiply(
            m1=model_transform,
            m2=pyrr.matrix44.create_from_translation(
                vec=np.array(self.position),dtype=np.float32
            )
        )

class VertexPoint:

  def __init__(self, index = 0, threshold = 0):
    self.setUpRadar(index=index)
    self.setUpThreshold(threshold)
    self.getVertices()

  def setUpRadar(self, index = 0,filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str = DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    self.radar = Grid(index, filePath, radarName, date, mode)

  def setUpThreshold(self, threshold = 0):
    self.threshold = threshold

  def getVertices(self):
    self.vertices = self.get_all_vertices_by_threshold()
    self.vertex_count = len(self.vertices) // 3
    self.vao = glGenVertexArrays(1)
    glBindVertexArray(self.vao)

    self.vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
    glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))

  def update(self):
    # self.radar.update()
    self.getVertices()

  def draw(self):
    # Draw the vertices (points)
    glDrawArrays(GL_POINTS, 0, self.vertex_count)

  def arm(self) -> None:
    glBindVertexArray(self.vao)

  def clear(self):
    self.radar = None
    self.vertices = []
    glDeleteVertexArrays(1, (self.vao,))
    glDeleteBuffers(1, (self.vbo,))

  def get_vertices_position(self, scaler):
    a = self.radar.data.z['data']
    b = self.radar.data.y['data']
    c = self.radar.data.x['data']

    # Create all combinations of indices
    idx_a, idx_b, idx_c = np.meshgrid(np.arange(len(a)), np.arange(len(b)), np.arange(len(c)), indexing='ij')
    combinations = np.array([c[idx_c.ravel()], b[idx_b.ravel()], a[idx_a.ravel()]]).T
    return scaler.fit_transform(
        combinations
    )

  def get_all_vertices_by_threshold(self, threshold = -20):
      reflectivity = self.radar.data.fields['reflectivity']['data'].flatten()

      indices = np.where(np.logical_and(np.logical_not(reflectivity.mask),reflectivity.data >= threshold))
      scaler = MinMaxScaler(feature_range=(-0.5, 0.5))
      vertices = self.get_vertices_position(scaler)
      return vertices[indices].flatten()