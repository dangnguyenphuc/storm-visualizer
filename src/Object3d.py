import numpy as np
from PIL import Image
import ctypes
import pyrr

from PyQt5 import QtOpenGL
from PyQt5.QtGui import QColor

from OpenGL import GLU
import OpenGL.GL as gl
from OpenGL.arrays import vbo

from Radar import *
from Utils import read_shader

class Entity:

    def __init__(self, position: list[float], eulers: list[float], scale: float = 1):
        self.scale = scale
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
    
    def updateScale(self, val) ->None:
        self.scale = val

    def updateY(self, val) -> None:
        self.eulers[1] = val

        if self.eulers[1] >= 360:
            self.eulers[1] = 360
        elif self.eulers[1] <=0:
            self.eulers[1] = 0

    def updateX(self, val) -> None:
        self.eulers[0] = val

        if self.eulers[0] >= 360:
            self.eulers[0] = 360
        elif self.eulers[0] <=0:
            self.eulers[0] = 0

    def updateZ(self, val) -> None:

        self.eulers[2] = val

        if self.eulers[2] >= 360:
            self.eulers[2] = 360
        elif self.eulers[2] <=0:
            self.eulers[2] = 0

    def getModelTransform(self) -> np.ndarray:

        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        for i in range(3):
          axis = [0,0,0]
          axis[i] = 1
          model_transform = pyrr.matrix44.multiply(
            m1=model_transform,
            m2=pyrr.matrix44.create_from_axis_rotation(
                axis=axis,  # Y-axis
                theta=np.radians(self.eulers[i]),
                dtype=np.float32
              )
          )
        # Apply scaling
        scale_matrix = pyrr.matrix44.create_from_scale([self.scale] * 3)
        model_transform = pyrr.matrix44.multiply(model_transform, scale_matrix)

        # Apply translation
        translation_matrix = pyrr.matrix44.create_from_translation(
            vec=np.array(self.position),
            dtype=np.float32
        )
        model_transform = pyrr.matrix44.multiply(model_transform, translation_matrix)

        return model_transform

class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None, index = 0, threshold = 0):
        self.parent = parent
        super().__init__(parent)
        self.setUpRadar(index=0)
        self.setUpThreshold(threshold)
        
        self.mousePos = [0, 0] 
        self.zoom_center = [0, 0] 
        

    def setUpScale(self, val=1.0):
        self.entity.updateScale(val)

    def setUpRadar(self, index = 0, filePath: str = DEFAULT_FILE_PATH, radarName: str = DEFAULT_RADAR_NAME, year: str = DEFAULT_YEAR, month: str = DEFAULT_MONTH, day: str = DEFAULT_DATE, mode: str = DEFAULT_MODE):
        self.radar = Radar(index, filePath, radarName, year, month, day, mode)

    def resetRadar(self, DataManager: DataManager, index = 0):
        # del self.radar
        # self.radar = Radar(index, filePath, radarName, year, month, day, mode)
        DataManager.raw_data = DataManager.getAllDataFilePaths()
        self.radar.DataManager = DataManager
        self.radar.currentIndex = index

    def setUpThreshold(self, threshold = 0):
        self.threshold = threshold

    def update(self, index=None, threshold=None, clutterFilter = None, plot_mode = (None,0), flag = True):
        if index is not None:
            self.radar.update(index)
        if threshold is not None:
            self.threshold = threshold
            print(threshold)
        if clutterFilter is not None:
            self.radar.isFilterClutter(clutterFilter)
        if plot_mode[0] is not None:
            self.radar.plot(mode=plot_mode[0], sweep=plot_mode[1])

        if flag:
          self.clear()
          self.setUpVBO()
    
    def clear(self):
      try:
        gl.glDeleteBuffers(1, (self.vbo,))
      except:
        pass
    
    def createAssets(self):
      self.entity = Entity(
                  position = [0,0,-10],
                  eulers = [0,0,0],
                  scale= 1
        )
      codes = read_shader()
      self.program = gl.glCreateProgram()
      vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
      fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)

      # Set shaders source
      gl.glShaderSource(vertex, codes['vertex'])
      gl.glShaderSource(fragment, codes['fragment'])

      # Compile shaders
      gl.glCompileShader(vertex)
      if not gl.glGetShaderiv(vertex, gl.GL_COMPILE_STATUS):
          error = gl.glGetShaderInfoLog(vertex).decode()
          print("Vertex shader compilation error: %s", error)

      gl.glCompileShader(fragment)
      if not gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS):
          error = gl.glGetShaderInfoLog(fragment).decode()
          print(error)
          raise RuntimeError("Fragment shader compilation error")

      gl.glAttachShader(self.program, vertex)
      gl.glAttachShader(self.program, fragment)
      gl.glLinkProgram(self.program)

      if not gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS):
          print(gl.glGetProgramInfoLog(self.program))
          raise RuntimeError('Linking error')

      gl.glDetachShader(self.program, vertex)
      gl.glDetachShader(self.program, fragment)

      gl.glUseProgram(self.program)


    def initializeGL(self):
        self.qglClearColor(QColor(0, 0, 0))  
        gl.glEnable(gl.GL_DEPTH_TEST) 
        self.createAssets()
        self.setUpVBO()
        # self.loadMap()

    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)
        self.setUniforms(width=width, height=height, fovy=45.0, near=1.0, far=100)
        self.getUniformLocations()
        self.getModelTransform()

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glUseProgram(self.program)

        self.entity.position = [self.mousePos[0], self.mousePos[1] , self.entity.position[2]]

        self.getModelTransform()
        gl.glDrawArrays(gl.GL_POINTS, 0, len(self.vertices))
        
        # Clean up state
        gl.glUseProgram(0)

    def setUpVBO(self):
      # Build data
      v = self.radar.get_all_vertices_by_threshold(self.threshold)
      position = v['position']
      color = v['color']

      color = color[:, np.newaxis]
      self.vertices = np.concatenate((position, color), axis=1)

      try:
        # Request a buffer slot from GPU
        self.vbo = gl.glGenBuffers(1)

        # Make this buffer the default one
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)

        # Upload CPU data to GPU buffer
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, gl.GL_DYNAMIC_DRAW)

        positionLocation = gl.glGetAttribLocation(self.program, "position")
        gl.glEnableVertexAttribArray(positionLocation)
        gl.glVertexAttribPointer(positionLocation, 3, gl.GL_FLOAT, False, 16, ctypes.c_void_p(0))

        colorLocation = gl.glGetAttribLocation(self.program, "value")
        gl.glEnableVertexAttribArray(colorLocation)
        gl.glVertexAttribPointer(colorLocation, 1, gl.GL_FLOAT, False, 16, ctypes.c_void_p(12))
      except:
        pass

    def setRotX(self, val):
        self.entity.updateX(val * np.pi)

    def setRotY(self, val):
        self.entity.updateY(val * np.pi)

    def setRotZ(self, val):
        self.entity.updateZ(val * np.pi)

    def loadMap(self, filePath="map.png"):
      m = Image.open(filePath)
      mData = np.array(list(m.getdata()))
      self.mID = gl.glGenTextures(1)
      gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
      gl.glBindTexture(gl.GL_TEXTURE_2D, self.mID)
      gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
      gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
      gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
      gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
      gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BASE_LEVEL, 0)
      gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAX_LEVEL, 0)
      gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, m.size[0], m.size[1], 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, mData)
      m.close()


    def drawMap(self, centerX = 0, centerY = 0, centerZ = -1):
      verts = ((2, 2), (2, -2), (-2, -2), (-2, 2))
      texts = ((1, 0), (1, 1), (0, 1), (0, 0))
      surf = (0, 1, 2, 3)

      # Use shader program
      gl.glUseProgram(self.program)

      # Set uniform variables
      gl.glUniform1i(gl.glGetUniformLocation(self.program, "textureAvailable"), 1)
      gl.glUniform1i(gl.glGetUniformLocation(self.program, "imageTexture"), 0)

      # Bind texture
      gl.glActiveTexture(gl.GL_TEXTURE0)
      gl.glBindTexture(gl.GL_TEXTURE_2D, self.mID)

      # Set vertex attribute pointers
      gl.glEnableVertexAttribArray(2)
      gl.glVertexAttribPointer(2, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, verts)

      gl.glEnableVertexAttribArray(3)
      gl.glVertexAttribPointer(3, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, texts)

      # Draw quad
      gl.glDrawArrays(gl.GL_QUADS, 0, 4)

      # Clean up
      gl.glDisableVertexAttribArray(0)
      gl.glDisableVertexAttribArray(1)
      gl.glUseProgram(0)

    def setUniforms(self, width, height, fovy = 45, near = 1.0, far = 100) -> None:
      gl.glUseProgram(self.program)

      # Use orthographic projection
      projection_transform = pyrr.matrix44.create_perspective_projection(
          fovy = fovy, aspect = width/height,
          near = near, far = far, dtype=np.float32
      )

      # assign projection_transform to SHADER SCRIPT
      gl.glUniformMatrix4fv(
          gl.glGetUniformLocation(self.program, "projection"),
          1, gl.GL_FALSE, projection_transform
      )

    def getUniformLocations(self) -> None:
      """
          Query and store the locations of shader uniforms
      """

      gl.glUseProgram(self.program)
      self.modelMatrixLocation = gl.glGetUniformLocation(self.program, "model")

    def getModelTransform(self):
      gl.glUniformMatrix4fv(
          self.modelMatrixLocation, 1, gl.GL_FALSE,
          self.entity.getModelTransform()
      )
