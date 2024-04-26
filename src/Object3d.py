import numpy as np
from PIL import Image

from PyQt5 import QtOpenGL
from PyQt5.QtGui import QColor

from OpenGL import GLU
import OpenGL.GL as gl
from OpenGL.arrays import vbo

from Radar import *

class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None, index = 0, threshold = 0, format = None):
        self.parent = parent
        if format:
          super().__init__(format, parent)
        else:
          super().__init__(parent)
        self.setUpRadar(index=0)
        self.setUpThreshold(threshold)
        self.setUpScale()
        self.mousePos = [0, 0] 
        self.zoom_center = [0, 0] 
        self.scale = 1.0
    def setUpScale(self, val=1.0):
        self.scale = val

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

    def update(self, index=None, threshold=None, clutterFilter = None):
        if index is not None:
            self.radar.update(index)
        if threshold is not None:
            self.threshold = threshold
        if clutterFilter is not None:
            self.radar.isFilterClutter(clutterFilter)

        self.setUpVBO()

    def initializeGL(self):
        self.qglClearColor(QColor(0, 0, 0))  
        gl.glEnable(gl.GL_DEPTH_TEST)  
        self.setUpVBO()
        self.loadMap()

        self.rotX = 0.0
        self.rotY = 0.0
        self.rotZ = 0.0

    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect = width / float(height)

        # gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

        GLU.gluPerspective(45.0, aspect, 1.0, 100.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glPushMatrix()

        gl.glTranslate(self.mousePos[0], self.mousePos[1], -5.0)   
        gl.glTranslatef(self.zoom_center[0], self.zoom_center[1],  0)
        gl.glScale(self.scale, self.scale, self.scale) 
        gl.glTranslatef(-self.zoom_center[0], -self.zoom_center[1], 0) 
        gl.glRotate(self.rotX, 1.0, 0.0, 0.0)
        gl.glRotate(self.rotY, 0.0, 1.0, 0.0)
        gl.glRotate(self.rotZ, 0.0, 0.0, 1.0)

        self.drawMap()

        self.vertVBO.bind()
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, None)

        '''Comment these line when testing'''
        self.colorVBO.bind()
        gl.glEnableClientState(gl.GL_COLOR_ARRAY)
        gl.glColorPointer(3, gl.GL_FLOAT, 0, None)
        '''to this'''


        gl.glDrawArrays(gl.GL_POINTS, 0, len(self.vertices))
        # gl.glDrawArrays(gl.GL_POLYGON, 0, len(self.vertices))

        # Unbind and disable after drawing
        self.vertVBO.unbind()
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        '''Comment these line when testing'''
        self.colorVBO.unbind()
        gl.glDisableClientState(gl.GL_COLOR_ARRAY)
        '''to this'''
        self.drawMap()
        gl.glPopMatrix()

    def setUpVBO(self):

        v = self.radar.get_all_vertices_by_threshold(self.threshold)
        if v:
          self.vertices = v['position']

          '''Vertices for testing only, do not delete when complete'''
          # self.vertices = [
          #   [0.2, 0.1, 0],
          #   [0.1, 0.3, 0],
          #   [0.5, 0.05, 0],
          #   [0.32, 0.01, 0],
          #   [0.04, 0.04, 0],
          #   [0.32, 0.01, 0.5],
          #   [0.04, 0.5, 0.7]
          # ]

          self.vertVBO = vbo.VBO(np.reshape(self.vertices,
                                            (1, -1)).astype(np.float32))
          self.vertVBO.bind()

          self.color = v['color']
          self.colorVBO = vbo.VBO(np.reshape(self.color,
                                            (1, -1)).astype(np.float32))
          self.colorVBO.bind()

    def setRotX(self, val):
        self.rotX = np.pi * val

    def setRotY(self, val):
        self.rotY = np.pi * val

    def setRotZ(self, val):
        self.rotZ = np.pi * val

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
      verts = ((2, 2), (2,-2), (-2,-2), (-2,2))
      texts = ((1, 0), (1, 1), (0, 1), (0, 0))
      surf = (0, 1, 2, 3)

      gl.glEnable(gl.GL_TEXTURE_2D)
      gl.glBindTexture(gl.GL_TEXTURE_2D, self.mID)

      gl.glBegin(gl.GL_QUADS)
      for i in surf:
          gl.glTexCoord3f(texts[i][0], texts[i][1], 0)
          gl.glVertex3f(centerX + verts[i][0], centerY + verts[i][1], centerZ)  # Added centerZ
      gl.glEnd()
      
      gl.glDisable(gl.GL_TEXTURE_2D)
