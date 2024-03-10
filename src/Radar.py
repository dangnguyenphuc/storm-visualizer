import numpy as np
import pyart
import cartopy.crs as ccrs
import os

class DIRECTORY:
  FILE_PATH = "../Data/"
  RADAR_NAME = "NHB/"
  DATE = "01/"
  MODE = "1_prt/"

class DataManager:

  DATA = None
  NUM_OF_FILES = 0

  @staticmethod
  def getAllDataFilePaths(filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str = DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    filePaths = [
        fileName for fileName in os.listdir(
        filePath +
        radarName +
        date +
        mode)
        ]

    filePaths.sort()
    filePaths = [
        filePath +
        radarName +
        date +
        mode
        + fileName for fileName in filePaths
        ]

    DataManager.NUM_OF_FILES = len(filePaths)

    return filePaths

  @staticmethod
  def splitData(filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str = DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    print("Run splitData")
    print
    if radarName == "NHB/" and mode == "raw/":
      data = DataManager.getAllDataFilePaths(filePath, radarName, date, mode)
      one_prt = []
      two_prt = []

      for i in range(len(data)):
          if pyart.io.read(data[i]).instrument_parameters['prt_mode']['data'][0].decode() == 'fixed':
            one_prt.append(data[i])
          else: two_prt.append(data[i])

      firstDir = filePath + radarName + date + '1_prt/'
      secondDir = filePath + radarName + date + '2_prt/'

      print("Creating firstDir at: ", firstDir)
      print("Creating secondDir at: ", secondDir)

      os.mkdir(firstDir)
      os.mkdir(secondDir)

      for i in one_prt:
          os.rename(i, firstDir + i.split('/')[-1])
      for i in two_prt:
          os.rename(i, secondDir + i.split('/')[-1])

class Radar:

  def __init__(self, fileIndex = 0, filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str = DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    if not DataManager.DATA:
      DataManager.DATA = DataManager.getAllDataFilePaths(filePath, radarName, date, mode)

    self.currentIndex = fileIndex
    self.getRadar()

  def getRadar(self):
    self.data = pyart.io.read(DataManager.DATA[self.currentIndex])

  def increaseIndex(self):
    self.currentIndex += 1

    if (self.currentIndex >= DataManager.NUM_OF_FILES):
      self.currentIndex = 0

  def readDataFromFilePath(self, filePath: str):
    self.data = pyart.io.read(filePath)

  def readDataFromOtherMode(self, mode: str, fileIndex: int = 0):
    data = DataManager.getAllDataFilePaths(mode = mode)
    self.data = pyart.io.read(data[fileIndex])

  def readDataFromOtherDate(self, date: str, mode: str, fileIndex: int = 0):
    data = DataManager.getAllDataFilePaths(date = date, mode=mode)
    self.data = pyart.io.read(data[fileIndex])

  def update(self):
    self.increaseIndex()
    self.getRadar()