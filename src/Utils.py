from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
from matplotlib import cm
import calendar
from datetime import datetime

IGNOR_DIR = ["__pycache__", "icon", "style", "src"]

def listDirInDir(filePath):
    d = [
      dir for dir in os.listdir(filePath)
      if  not dir.startswith('.') and
          os.path.isdir(os.path.join(filePath, dir)) and
          dir not in IGNOR_DIR
    ]
    d.sort()
    return d

def folderEmpty(filePath):
    return len(os.listdir(filePath)) == 0

def is_valid_day_for_month_year(day, month_year):
    year, month = month_year.split('/')
    if not (1 <= int(month) <= 12):
        return False
    max_day = calendar.monthrange(int(year), int(month))[1]
    return 1 <= int(day) <= max_day

def is_safe_file(filename):
    unsafe_extensions = ['.exe', '.bat', '.sh', '.py']
    _, file_extension = os.path.splitext(filename)
    return file_extension.lower() not in unsafe_extensions

def listFile(folderPath):
    f = [
        file for file in os.listdir(folderPath)
        if  os.path.isfile(folderPath + file) and
            not file.startswith('.') and
            is_safe_file(file)
    ]
    f.sort(key=lambda e: e.split('.')[0])
    return f

def getYearMonthDate(radar):
    date_string = radar.time['units'].split(" ")[-1]
    dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")

    return (dt.year, dt.strftime("%m"), dt.strftime("%d"))

def create_shader(vertex_filepath: str, fragment_filepath: str) -> int:
    with open(vertex_filepath,'r') as f:
        vertex_src = f.readlines()

    with open(fragment_filepath,'r') as f:
        fragment_src = f.readlines()

    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                            compileShader(fragment_src, GL_FRAGMENT_SHADER))

    return shader

def color(value):
    normalized_values = (value - 0) / (65 - 0)
    colors = np.zeros((len(value), 3))
    colors[:, 0] = 0.2 + normalized_values # Red channel
    colors[:, 1] = normalized_values        # Green channel
    colors[:, 2] = 0.6-normalized_values     # Blue channel
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


