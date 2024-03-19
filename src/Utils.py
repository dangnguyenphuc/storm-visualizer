import pygame
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileProgram,compileShader

from Config import *

def create_shader(vertex_filepath: str, fragment_filepath: str) -> int:
    """
        Compile and link shader modules to make a shader program.

        Parameters:

            vertex_filepath: path to the text file storing the vertex
                            source code

            fragment_filepath: path to the text file storing the
                                fragment source code

        Returns:

            A handle to the created shader program
    """

    with open(vertex_filepath,'r') as f:
        vertex_src = f.readlines()

    with open(fragment_filepath,'r') as f:
        fragment_src = f.readlines()

    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                            compileShader(fragment_src, GL_FRAGMENT_SHADER))

    return shader

def drawTextOnScreen(surface, text, font, textColor, x, y):

    img = font.render(text, True, textColor)
    surface.blit(img, (x,y))

def convertGameTime2Minute(time):
    minute = (time // WINDOW_PROPERTIES.FPS) // 60
    second = (time // WINDOW_PROPERTIES.FPS) - 60 * minute
    return "{:02d}:{:02d}".format(minute, second)

class Timer:
    def __init__(self, time ,fps=WINDOW_PROPERTIES.FPS):
        self.time = time*fps
        self.currentTime = time*fps
        self.flag = False

    def run(self):
        self.currentTime -= 1

        if self.currentTime <= 0:
            self.flag = True

    def reset(self):
        self.flag = False
        self.currentTime = self.time

    def removeAndSetOtherTime(self, time, fps=WINDOW_PROPERTIES.FPS):
        self.time = time*fps
        self.currentTime = time*fps
        self.flag = False


