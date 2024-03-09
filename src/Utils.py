import pygame

def drawTextOnScreen(surface, text, font, textColor, x, y):

    img = font.render(text, True, textColor)
    surface.blit(img, (x,y))

def convertGameTime2Minute(time):
    minute = (time // FPS) // 60
    second = (time // FPS) - 60 * minute
    return "{:02d}:{:02d}".format(minute, second)

class Timer:
    def __init__(self, time ,fps=FPS):
        self.time = time*FPS
        self.currentTime = time*FPS
        self.flag = False

    def getFlag(self):
        return self.flag

    def run(self):
        self.currentTime -= 1

        if self.currentTime <= 0:
            self.flag = True

    def reset(self):
        self.flag = False
        self.currentTime = self.time

    def removeAndSetOtherTime(self, time, fps=FPS):
        self.time = time*FPS
        self.currentTime = time*FPS
        self.flag = False

    def getTime(self):
        return self.time//FPS


