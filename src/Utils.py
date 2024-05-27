
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import calendar
from datetime import datetime
from Config import TICK

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileProgram,compileShader

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
  if os.path.exists(filePath):
    return len(os.listdir(filePath)) == 0
  else: 
    print(f'No such file or dir: {filePath}')

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

def getHourMinuteSecond(radar):
    date_string = radar.time['units'].split(" ")[-1]
    dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")

    return (dt.strftime("%H"), dt.strftime("%M"), dt.strftime("%S"))


def read_shader(vertex_filepath: str = "shaders/vertex.txt", fragment_filepath: str = "shaders/fragment.txt") -> int:
    with open(vertex_filepath,'r') as f:
        vertex_src = f.readlines()

    with open(fragment_filepath,'r') as f:
        fragment_src = f.readlines()

    return {
      'vertex': vertex_src,
      'fragment': fragment_src
    }

def color(value):
    normalized_values = (value + 0) / (65 + 0)
    colors = np.zeros((len(value), 3))
    colors[:, 0] = 0.3 + normalized_values # Red channel
    colors[:, 1] = normalized_values        # Green channel
    colors[:, 2] = 0.8-normalized_values     # Blue channel
    return colors