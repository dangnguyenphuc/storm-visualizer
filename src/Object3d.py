import numpy as np
from PIL import Image

from PyQt5 import QtOpenGL
from PyQt5.QtGui import QColor

from OpenGL import GLU
import OpenGL.GL as gl
from OpenGL.arrays import vbo

from Radar import *

colors = [
  (1.0, 0.0, 0.0),  # Red
  (0.0, 1.0, 0.0),  # Green
  (1.0, 1.0, 0.0),  # Yellow
  (0.0, 0.0, 1.0),  # Blue
  (1.0, 0.0, 1.0),  # Pink
  (1.0, 0.5, 0.0),  # Orange
  (1.0, 1.0, 1.0)
]  

class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None, index = 0, threshold = 0, format = None, DataManager = None):
        self.parent = parent
        self.plotThread = None
        if format:
          super().__init__(format, parent)
        else:
          super().__init__(parent)

        self.setUpRadar(index=0)
        self.setUpThreshold(threshold)
        self.setUpScale()

        self.isGrid = False

        self.vertices = []
        self.vertVBO = None
        self.color = []
        self.colorVBO = None

        self.stormVBO = []
        self.stormSideVBO = []

        self.tracksVBO = []
        self.tracksVertices = []

        self.mousePos = [0, 0] 
        self.zoom_center = [0, 0] 

        if DataManager is not None:
          self.radar.DataManager = DataManager
        
    def setUpScale(self, val=1.0):
        self.scale = val

    def setUpRadar(
          self, 
          index = 0, 
          filePath: str = DEFAULT_FILE_PATH, 
          radarName: str = DEFAULT_RADAR_NAME, 
          year: str = DEFAULT_YEAR, 
          month: str = DEFAULT_MONTH, 
          day: str = DEFAULT_DATE, 
          mode: str = DEFAULT_MODE):

        self.radar = Radar(index, filePath, radarName, year, month, day, mode)

    def resetRadar(self, DataManager: DataManager, index = 0):
        DataManager.raw_data = DataManager.getAllDataFilePaths()
        self.radar.DataManager = DataManager
        self.radar.currentIndex = index

    def setUpThreshold(self, threshold = 0):
        self.threshold = threshold

    def update(self, index=None, threshold=None, clutterFilter = None, isGrid = None, plot_mode = (None,0), flag = True):
        if index is not None:
            self.radar.update(index)
        if threshold is not None:
            self.threshold = threshold
        if clutterFilter is not None:
            self.radar.isFilterClutter(clutterFilter)
        if plot_mode[0] is not None:
            self.radar.plot(mode=plot_mode[0], sweep=plot_mode[1])
        if isGrid is not None:
            self.radar.update(isGrid=isGrid)

        if flag:
          self.setUpVBO()

        if isGrid:
          self.stormLayer, self.stormSide = self.radar.getAllStormVertices()
          self.setUpStorm()

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

        GLU.gluPerspective(45.0, aspect, 1.0, 10.0)
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
        self.renderRaw()

        # render tracks
        if self.radar.isGrid and len(self.tracksVBO) > 0:
          self.renderStorm()
          for i in range(len(self.tracksVBO)):
            self.tracksVBO[i].bind()
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glVertexPointer(3, gl.GL_FLOAT, 0, None)
            gl.glLineWidth(5.0)
            gl.glPointSize(5.0);
            gl.glColor3f(colors[i%len(colors)][0], colors[i%len(colors)][1], colors[i%len(colors)][2])
            if len(self.tracksVertices[i]) == 1:
              gl.glDrawArrays(gl.GL_POINTS, 0, len(self.tracksVertices[i]))
            else:
              gl.glDrawArrays(gl.GL_LINE_STRIP, 0, len(self.tracksVertices[i]))
            self.tracksVBO[i].unbind()

        gl.glPointSize(1.0);
        gl.glLineWidth(1.0)
        gl.glColor3f(1.0, 1.0, 1.0)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glPopMatrix()

    def renderRaw(self):

      self.vertVBO.bind()
      gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
      gl.glVertexPointer(3, gl.GL_FLOAT, 0, None)

      """Comment these line when testing"""
      self.colorVBO.bind()
      gl.glEnableClientState(gl.GL_COLOR_ARRAY)
      gl.glColorPointer(3, gl.GL_FLOAT, 0, None)
      """to this"""


      gl.glDrawArrays(gl.GL_POINTS, 0, len(self.vertices))

      # Unbind and disable after drawing
      self.vertVBO.unbind()
      
      """Comment these line when testing"""
      self.colorVBO.unbind()
      gl.glDisableClientState(gl.GL_COLOR_ARRAY)
      """to this"""


    def setUpVBO(self, flag = True):

        if flag:
          v = self.radar.get_all_vertices_by_threshold(self.threshold)
        else:
          v = self.radar.get_all_vertices()

        del self.vertices, self.color
        if self.vertVBO:
          self.vertVBO.delete()
        if self.colorVBO:
          self.colorVBO.delete()
          
        self.vertices = v['position']
        self.vertVBO = vbo.VBO(np.reshape(self.vertices,
                                          (1, -1)).astype(np.float32))
        self.vertVBO.bind()
        self.color = v['color']
        self.colorVBO = vbo.VBO(np.reshape(self.color,
                                          (1, -1)).astype(np.float32))
        self.colorVBO.bind()

        if self.radar.isGrid and 'trackLines' in v:
          if len(self.tracksVBO) > 0:
            for i in (self.tracksVBO).copy():
              i.delete()
              self.tracksVBO.remove(i)

          if len(v['trackLines']) > 0:
            self.tracksVBO = []
            self.tracksVertices = []
            self.tracksVertices.clear()
            for i in v['trackLines']:
              self.tracksVertices.append(v['trackLines'][i])
              vertVBO = vbo.VBO(np.reshape(v['trackLines'][i],
                                      (1, -1)).astype(np.float32))
              self.tracksVBO.append(vertVBO)

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

    def setUpStorm(self):
      
      # clear up before setting VBO
      if len(self.stormVBO) > 0:
        for i in (self.stormVBO).copy():
          for layer in i:
            layer.delete()
          self.stormVBO.remove(i)
        self.stormVBO.clear()
        
      if len(self.stormSideVBO) > 0:
        for i in (self.stormSideVBO).copy():
          i.delete()
          self.stormSideVBO.remove(i)
        self.stormSideVBO.clear()
          
      if self.stormSide and self.stormLayer and len(self.stormSide) > 0 and len(self.stormLayer) > 0:
        self.stormVBO = []
        for i in range(len(self.stormLayer)):
          stormVBO = []
          for j in range(len(self.stormLayer[i])):
            vertVBO = vbo.VBO(np.reshape(self.stormLayer[i][j],
                                      (1, -1)).astype(np.float32))
            stormVBO.append(vertVBO)
          self.stormVBO.append(stormVBO)

        self.stormSideVBO = []
        self.stormSideLine = []
        for i in range(len(self.stormSide)):
          stormSideLine = []
          for j in range(len(self.stormSide[i])):
            for k in range(len(self.stormSide[i][j])):
              if k < len(self.stormLayer[i][j]):
                for z in range(len(self.stormLayer[i][j]), len(self.stormSide[i][j])):
                    stormSideLine.append(self.stormSide[i][j][k])
                    stormSideLine.append(self.stormSide[i][j][z])
              else: continue
          self.stormSideLine.append(stormSideLine)
          self.stormSideVBO.append(vbo.VBO(np.reshape(stormSideLine,
                                      (1, -1)).astype(np.float32)))
    
    def renderStorm(self):
      if len(self.stormVBO) > 0:
        for i in range(len(self.stormSideVBO)):
          self.stormSideVBO[i].bind()
          gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
          gl.glVertexPointer(3, gl.GL_FLOAT, 0, None)
          gl.glDrawArrays(gl.GL_LINES, 0, len(self.stormSideLine[i]))
          self.stormSideVBO[i].unbind()

        for i in range(len(self.stormVBO)):
          for j in range(len(self.stormVBO[i])):
            self.stormVBO[i][j].bind()
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glVertexPointer(3, gl.GL_FLOAT, 0, None)
            gl.glDrawArrays(gl.GL_POLYGON, 0, len(self.stormLayer[i][j]))
            self.stormVBO[i][j].unbind()