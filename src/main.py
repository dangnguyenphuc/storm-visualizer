# from App import *

# if __name__ == "__main__":
#   app = App()
#   app.run()
#   app.destroy()

import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr
from Vertex import *
from Utils import Timer


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

    def update(self) -> None:
        """
            Update the object, this is hard coded for now.
        """

        self.eulers[1] += 0.25

        if self.eulers[1] > 360:
            self.eulers[1] -= 360

    def get_model_transform(self) -> np.ndarray:
        """
            Returns the entity's model to world
            transformation matrix.
        """

        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)

        model_transform = pyrr.matrix44.multiply(
            m1=model_transform,
            m2=pyrr.matrix44.create_from_axis_rotation(
                axis = [0, 1, 0],
                theta = np.radians(self.eulers[1]),
                dtype = np.float32
            )
        )

        return pyrr.matrix44.multiply(
            m1=model_transform,
            m2=pyrr.matrix44.create_from_translation(
                vec=np.array(self.position),dtype=np.float32
            )
        )

class App:
    """
        For now, the app will be handling everything.
        Later on we'll break it into subcomponents.
    """


    def __init__(self):
        """ Initialise the program """

        self._set_up_pygame()

        self._set_up_timer()

        self._set_up_opengl()

        self._create_assets()

        self._set_onetime_uniforms()

        self._get_uniform_locations()

    def _set_up_pygame(self) -> None:
        """
            Initialize and configure pygame.
        """

        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode((640,480), pg.OPENGL|pg.DOUBLEBUF)

    def _set_up_timer(self) -> None:
        """
            Set up the app's timer.
        """

        self.clock = pg.time.Clock()

    def _set_up_opengl(self) -> None:
        """
            Configure any desired OpenGL options
        """

        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)

    def _create_assets(self) -> None:
        """
            Create all of the assets needed for drawing.
        """

        self.cube = Entity(
            position = [0,0,-3],
            eulers = [0,0,0]
        )
        self.cube_mesh = CubeMesh()
        self.shader = create_shader(
            vertex_filepath = "shaders/vertex.txt",
            fragment_filepath = "shaders/fragment.txt")

    def _set_onetime_uniforms(self) -> None:
        """
            Some shader data only needs to be set once.
        """

        glUseProgram(self.shader)

        # Use orthographic projection
        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = 640/480,
            near = 1.0, far = 10, dtype=np.float32
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.shader,"projection"),
            1, GL_FALSE, projection_transform
        )

    def _get_uniform_locations(self) -> None:
        """
            Query and store the locations of shader uniforms
        """

        glUseProgram(self.shader)
        self.modelMatrixLocation = glGetUniformLocation(self.shader,"model")

    def run(self) -> None:
        """ Run the app """

        running = True
        while (running):
            #check events
            for event in pg.event.get():
                if (event.type == pg.QUIT):
                    running = False

            #update cube
            # self.cube.update()

            #refresh screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glUseProgram(self.shader)


            glUniformMatrix4fv(
                self.modelMatrixLocation, 1, GL_FALSE,
                self.cube.get_model_transform())
            self.cube_mesh.arm_for_drawing()
            self.cube_mesh.draw()

            pg.display.flip()

            #timing
            self.clock.tick(60)

    def quit(self) -> None:
        """ cleanup the app, run exit code """

        self.cube_mesh.destroy()
        glDeleteProgram(self.shader)
        pg.quit()

class CubeMesh:
    """
        Used to draw a cube.
    """

    def __init__(self):
        """
            Initialize a cube.
        """

        # Vertices for a cube
        self.timer = Timer(0.5)
        self.vertex = VertexPoint(threshold=35)

        vertices = np.array(self.vertex.vertices, dtype=np.float32)
        self.vertex_count = len(vertices) // 3
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))

    def arm_for_drawing(self) -> None:
        """
            Arm the cube for drawing.
        """
        self.timer.run()

        if self.timer.flag:
          self.vertex.update()
          vertices = np.array(self.vertex.vertices, dtype=np.float32)
          self.vertex_count = len(vertices) // 3
          glBindVertexArray(self.vao)

          glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
          glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

          self.timer.reset()


        glBindVertexArray(self.vao)

    def draw(self) -> None:
        """
            Draw the cube.
        """
        glDrawArrays(GL_POINTS, 0, self.vertex_count)

    def destroy(self) -> None:
        """
            Free any allocated memory.
        """
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

if __name__ == '__main__':

  my_app = App()
  my_app.run()
  my_app.quit()