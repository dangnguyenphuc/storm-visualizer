from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
from matplotlib import cm

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

def color(value):
    """
    Generate colors based on input values.

    Args:
        value: Array of values.

    Returns:
        colors: Array of RGB colors corresponding to input values.
    """
    # Normalize values to range [0, 1]
    normalized_values = (value - 0) / (80 - 0)

    # Map normalized values to RGB colors
    # Here is a simple example, you can modify this for your specific color scheme
    colors = np.zeros((len(value), 3))
    colors[:, 0] = 1.0 - normalized_values # Red channel
    colors[:, 1] = normalized_values        # Green channel
    colors[:, 2] = 1.0       # Blue channel
    return colors

class Timer:
    def __init__(self, time):
        self.time = time
        self.currentTime = time
        self.flag = False

    def run(self):
        self.currentTime -= 1

        if self.currentTime <= 0:
            self.flag = True

    def reset(self):
        self.flag = False
        self.currentTime = self.time

    def removeAndSetOtherTime(self, time):
        self.time = time
        self.currentTime = time
        self.flag = False


