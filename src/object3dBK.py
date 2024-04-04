from PyQt5 import QtCore      # core Qt functionality
from PyQt5 import QtWidgets       # extends QtCore with GUI functionality
from PyQt5 import QtOpenGL    # provides QGLWidget, a special OpenGL QWidget
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QAction, QMenu, QPushButton
import OpenGL.GL as gl        # python wrapping of OpenGL
from OpenGL import GLU        # OpenGL Utility Library, extends OpenGL functionality

import sys                    # we'll need this later to run our Qt application

from OpenGL.arrays import vbo
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from Radar import *
from Utils import color


class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None, index = 0, threshold = 0):
        self.parent = parent
        super().__init__(parent)
        self.setUpRadar(index=index)
        self.setUpThreshold(threshold)

    def setUpRadar(self, index = 0,filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str = DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
        self.radar = Radar(index, filePath, radarName, date, mode)
    def setUpThreshold(self, threshold = 0):
        self.threshold = threshold

    def initializeGL(self):
        self.qglClearColor(QColor(0, 0, 0))    # initialize the screen to blue
        gl.glEnable(gl.GL_DEPTH_TEST)                  # enable depth testing

        self.initGeometry()

        self.rotX = 0.0
        self.rotY = 0.0
        self.rotZ = 0.0

    def resizeGL(self, width, height):
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect = width / float(height)

        GLU.gluPerspective(45.0, aspect, 1.0, 100.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glPushMatrix()    # push the current matrix to the current stack

        gl.glTranslate(0.0, 0.0, -5.0)    # third, translate cube to specified depth
        gl.glScale(1.5, 1.5, 1.5)       # second, scale cube
        gl.glRotate(self.rotX, 1.0, 0.0, 0.0)
        gl.glRotate(self.rotY, 0.0, 1.0, 0.0)
        gl.glRotate(self.rotZ, 0.0, 0.0, 1.0)

        self.vertVBO.bind()
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, None)

        self.colorVBO.bind()
        gl.glEnableClientState(gl.GL_COLOR_ARRAY)
        gl.glColorPointer(3, gl.GL_FLOAT, 0, None)

        gl.glDrawElements(gl.GL_POINTS, len(self.cubeIdxArray), gl.GL_UNSIGNED_INT, self.cubeIdxArray)

        # Unbind and disable after drawing
        self.vertVBO.unbind()
        self.colorVBO.unbind()
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_COLOR_ARRAY)

        gl.glPopMatrix()    # restore the previous modelview matrix

    def initGeometry(self):

        v = self.get_all_vertices_by_threshold()
        self.cubeVtxArray = v['position']
        self.vertVBO = vbo.VBO(np.reshape(self.cubeVtxArray,
                                          (1, -1)).astype(np.float32))
        self.vertVBO.bind()

        self.cubeClrArray = v['color']
        self.colorVBO = vbo.VBO(np.reshape(self.cubeClrArray,
                                           (1, -1)).astype(np.float32))
        self.colorVBO.bind()

        self.cubeIdxArray = np.array(range(len(self.cubeVtxArray)))

    def setRotX(self, val):
        self.rotX = np.pi * val

    def setRotY(self, val):
        self.rotY = np.pi * val

    def setRotZ(self, val):
        self.rotZ = np.pi * val

    def get_vertices_positionX(self, indices=None):
        if indices:
            return self.radar.data.gate_x["data"][indices]
        else:  return self.radar.data.gate_x["data"]

    def get_vertices_positionY(self, indices=None):
        if indices:
            return self.radar.data.gate_y["data"][indices]
        else:  return self.radar.data.gate_y["data"]

    def get_vertices_positionZ(self, indices=None):
        if indices:
            return self.radar.data.gate_z["data"][indices]
        else:  return self.radar.data.gate_z["data"]

    def get_vertices_position(self, scaler):
        return scaler.fit_transform(
            np.column_stack(
                (
                self.radar.data.gate_x["data"].flatten(),
                self.radar.data.gate_y["data"].flatten(),
                self.radar.data.gate_z["data"].flatten()
                )
            )
        )

    def get_all_vertices_by_threshold(self):
        reflectivity = self.radar.data.fields['reflectivity']['data'].flatten()

        indices = np.where(np.logical_and(np.logical_not(reflectivity.mask), reflectivity.data >= self.threshold))
        scaler = MinMaxScaler(feature_range=(-1.0, 1.0))
        vertices = self.get_vertices_position(scaler)
        return {
            'position': vertices[indices],
            'color': color(reflectivity[indices])
        }

