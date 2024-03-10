import pygame
from Config import *

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


