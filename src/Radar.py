import numpy as np
import pyart
import cartopy.crs as ccrs
import os
from sklearn.preprocessing import MinMaxScaler
from Utils import listDirInDir, listFile, is_valid_day_for_month_year, color, getYearMonthDate
import wradlib as wrl
import xarray
import pandas as pd
from tint.grid_utils import *

class DIRECTORY:
  FILE_PATH = "../Data/"
  RADAR_NAME = "NHB/"
  YEAR = "2023/"
  MONTH = "06/"
  DATE = "01/"
  MODE = "1_prt/"

  @staticmethod
  def getCurrentPath(filename = False, radar = False, year = False, month = False, date = False, mode = False):
    if filename:
      return DIRECTORY.FILE_PATH

    if radar:
      return DIRECTORY.FILE_PATH + DIRECTORY.RADAR_NAME

    if year:
      return DIRECTORY.FILE_PATH + DIRECTORY.RADAR_NAME + DIRECTORY.YEAR

    if month:
      return DIRECTORY.FILE_PATH + DIRECTORY.RADAR_NAME + DIRECTORY.YEAR + DIRECTORY.MONTH

    if date:
      return DIRECTORY.FILE_PATH + DIRECTORY.RADAR_NAME + DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE

    if mode:
      return DIRECTORY.FILE_PATH + DIRECTORY.RADAR_NAME + DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE + DIRECTORY.MODE

class DataManager:

  RAW_DATA = None
  GRID_DATA = None
  NUM_OF_RAW_FILES = 0
  NUM_OF_GRID_FILES = 0

  @staticmethod
  def getAllDataFilePaths(filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str =DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    filePaths = [
        filePath + radarName + date + mode + fileName for fileName in DataManager.listAllFile(
        filePath,
        radarName,
        date,
        mode)
        ]

    if "grid" not in mode:
      DataManager.NUM_OF_RAW_FILES = len(filePaths)
    else:
      DataManager.NUM_OF_GRID_FILES = len(filePaths)

    return filePaths

  @staticmethod
  def reconstructFile(filePath: str = DIRECTORY.FILE_PATH):

    def loopThroughFiles(files):
      loopPath = []
      for file in files:
        try:
          radar = pyart.io.read(filePath + file)
          radarName = radar.metadata["instrument_name"].decode() + '/'
          if not os.path.exists(filePath + radarName):
            os.makedirs(filePath + radarName)

          year, month, date = getYearMonthDate(radar)
          path = filePath + radarName + str(year) + "/" + str(month) + "/" + str(date) + "/"
          if not os.path.exists(path):
            os.makedirs(path)
            loopPath.append({
              "filePath": filePath,
              "radarName": radarName,
              "date": str(year) + "/" + str(month) + "/" + str(date) + "/"
            })

          # mv filePath+file path+file
          os.rename(filePath + file, path + file)
        except:
          continue


      for path in loopPath:
        DataManager.splitData(filePath=path["filePath"], radarName=path["radarName"], date=path["date"], mode="")

    try:
      folder = listDirInDir(filePath)
      if len(folder) > 0:
        currentFolder = folder[0]
        while len(folder):
          for item in os.listdir(filePath + currentFolder):
            os.rename(filePath + currentFolder + "/" + item, filePath + item)

          os.rmdir(filePath + currentFolder)
          folder = listDirInDir(filePath)
          if len(folder) > 0:
            currentFolder = folder[0]
          else: break

      files = listFile(filePath)
      if len(files):
        loopThroughFiles(files=files)
    except Exception as e:
      print(e)

  @staticmethod
  def splitData(filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str =DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    if mode == "raw/" or not mode or mode == "":
      data = DataManager.getAllDataFilePaths(filePath, radarName, date, mode)
      fixed = []
      dual = []
      staggered = []
      other = []

      for i in range(len(data)):
        radar = pyart.io.read(data[i])
        if radar.instrument_parameters['prt_mode']['data'][0].decode() == 'fixed' or len(radar.instrument_parameters['prt_mode']['data']) == 0:
          fixed.append(data[i])
        elif radar.instrument_parameters['prt_mode']['data'][0].decode() == 'dual' : dual.append(data[i])
        elif radar.instrument_parameters['prt_mode']['data'][0].decode() == 'staggered' : staggered.append(data[i])
        else: other.append(data[i])

      if len(fixed) > 0:
        firstDir = filePath + radarName + date + 'fixed/'
        if not os.path.exists(firstDir):
          os.mkdir(firstDir)
      if len(dual) > 0:
        secondDir = filePath + radarName + date + 'dual/'
        if not os.path.exists(secondDir):
          os.mkdir(secondDir)
      if len(staggered) > 0:
        thirdDir = filePath + radarName + date + 'staggered/'
        if not os.path.exists(thirdDir):
          os.mkdir(thirdDir)
      if len(other) > 0:
        fourthDir = filePath + radarName + date + 'staggered/'
        if not os.path.exists(fourthDir):
          os.mkdir(fourthDir)

      for i in fixed:
        os.rename(i, firstDir + i.split('/')[-1])
      for i in dual:
        os.rename(i, secondDir + i.split('/')[-1])
      for i in staggered:
        os.rename(i, thirdDir + i.split('/')[-1])
      for i in other:
        os.rename(i, fourthDir + i.split('/')[-1])

      if mode: os.rmdir(filePath + radarName + date + mode)

  @staticmethod
  def genGrid(filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str =DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    def get_grid(radar):
      """ Returns grid object from radar object. """
      grid = pyart.map.grid_from_radars(
          radar, grid_shape=(5, 1000, 1000),
          grid_limits=((0, 25000), (-330000,330000), (-330000, 330000)),
          fields=['reflectivity'], gridding_algo='map_gates_to_grid',
          h_factor=0., nb=0.6, bsp=1., min_radius=200.)
      return grid

    def write_grid():
        tmp_dir = filePath + radarName + date + "grid/" + mode
        if not os.path.exists(tmp_dir):
          os.makedirs(tmp_dir)

        keys = DataManager.getAllDataFilePaths(filePath=filePath, radarName=radarName, date=date, mode=mode)
        for key in keys:
            radar = pyart.io.read(key)
            grid = get_grid(radar)
            pyart.io.write_grid(tmp_dir + 'grid_' + key.split("/")[-1].split(".")[0] + '.nc', grid)
            del radar, grid

    write_grid()

  @staticmethod
  def listAllRadar(filePath=DIRECTORY.FILE_PATH):
    return listDirInDir(filePath)

  @staticmethod
  def listAllDateOfRadar(filePath=DIRECTORY.FILE_PATH, radar=DIRECTORY.RADAR_NAME):
    years = [year for year in listDirInDir(filePath+radar) if year.isdigit()]
    if len(years) == 0:
      return None

    months = []
    for year in years:
      months += [year + "/" + month for month in listDirInDir(filePath + radar + year) if month.isdigit() and int(month) <= 12 and int(month) > 0]
    if len(months) == 0:
      return None

    dates = []
    for month in months:
      dates += [month + "/" + date for date in listDirInDir(filePath + radar + month) if date.isdigit() and is_valid_day_for_month_year(date, month)]
    if len(dates) == 0:
      return None

    return dates

  @staticmethod
  def listAllModeOnDate(filePath=DIRECTORY.FILE_PATH, radar=DIRECTORY.RADAR_NAME, date=DIRECTORY.YEAR+DIRECTORY.MONTH+DIRECTORY.DATE):
    mode = listDirInDir(filePath+radar+date)
    if "grid" in mode:
      mode.remove("grid")
    return mode

  @staticmethod
  def listAllFile(filePath=DIRECTORY.FILE_PATH, radar=DIRECTORY.RADAR_NAME, date=DIRECTORY.YEAR+DIRECTORY.MONTH+DIRECTORY.DATE, mode=DIRECTORY.MODE):
    return listFile(filePath + radar + date + mode)

class Radar:

  def __init__(self, fileIndex = 0, filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str =DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    DataManager.RAW_DATA = DataManager.getAllDataFilePaths(filePath, radarName, date, mode)

    self.currentIndex = fileIndex
    self.getRadar()

  def getRadar(self):
    self.data = pyart.io.read(DataManager.RAW_DATA[self.currentIndex])
    self.currentReflectivity = self.data.fields['reflectivity']['data'].flatten()

  def increaseIndex(self):
    self.currentIndex += 1

    if (self.currentIndex >= DataManager.NUM_OF_RAW_FILES):
      self.currentIndex = 0

  def readDataFromFilePath(self, filePath: str):
    self.data = pyart.io.read(filePath)

  def readDataFromOtherMode(self, mode: str, fileIndex: int = 0):
    data = DataManager.getAllDataFilePaths(mode = mode)
    self.data = pyart.io.read(data[fileIndex])

  def readDataFromOtherDate(self, date: str, mode: str, fileIndex: int = 0):
    data = DataManager.getAllDataFilePaths(date = date, mode=mode)
    self.data = pyart.io.read(data[fileIndex])

  def update(self, index = None):
    if index is not None:
      self.currentIndex = index
    else:
      self.increaseIndex()

    self.getRadar()


  def get_vertices_positionX(self, indices=None):
        if indices is not None:
            return self.data.gate_x["data"][indices]
        else:  return self.data.gate_x["data"]

  def get_vertices_positionY(self, indices=None):
      if indices is not None:
          return self.data.gate_y["data"][indices]
      else:  return self.data.gate_y["data"]

  def get_vertices_positionZ(self, indices=None):
      if indices is not None:
          return self.data.gate_z["data"][indices]
      else:  return self.data.gate_z["data"]

  def get_vertices_position(self, scaler):
      return scaler.fit_transform(
          np.column_stack(
              (
              self.data.gate_x["data"].flatten(),
              self.data.gate_y["data"].flatten(),
              self.data.gate_z["data"].flatten()
              )
          )
      )

  def get_all_vertices_by_threshold(self, threshold = 0):

      indices = np.where(np.logical_and(np.logical_not(self.currentReflectivity.mask), self.currentReflectivity.data >= threshold))
      scaler = MinMaxScaler(feature_range=(-1.0, 1.0))
      vertices = self.get_vertices_position(scaler)
      return {
          'position': vertices[indices],
          'color': color(self.currentReflectivity[indices])
      }

  def isFilterClutter(self, isFilter = False):
    def get_DBZ_from_sweep(radar, sweep = 1):
      try:
        return radar["data"][sweep]["sweep_data"]["DB_DBZ2"]
      except Exception as e:
        return radar["data"][sweep]["sweep_data"]["DB_DBZ"]

    if isFilter:
      data = np.ma.filled(self.data.fields['reflectivity']['data'], fill_value=-327)
      site = (self.data.longitude['data'][0], self.data.latitude['data'][0], self.data.altitude['data'][0])
      r = self.data.range['data']

      self.currentReflectivity = np.ma.masked_array(np.empty((0, self.data.ngates)), mask=np.empty((0, self.data.ngates), dtype=bool))
      for sweep in range(self.data.nsweeps):

        da = wrl.georef.create_xarray_dataarray(
            data[self.data.get_start(sweep) : self.data.get_end(sweep) + 1],
            phi=self.data.get_azimuth(sweep),
            theta=self.data.get_elevation(sweep),
            r=r,
            site=site
        ).wrl.georef.georeference()
        clutter = da.wrl.classify.filter_gabella(tr1=12, n_p=6, tr2=1.1)
        data_no_clutter = da.wrl.ipol.interpolate_polar(clutter)
        masked_array = np.ma.masked_array(data_no_clutter, mask=data_no_clutter < -327, fill_value=None)

        self.currentReflectivity = np.ma.concatenate((self.currentReflectivity, masked_array), axis=0)

      self.currentReflectivity = self.currentReflectivity.flatten()

    else:
      self.currentReflectivity = self.data.fields['reflectivity']['data'].flatten()
class Grid:

  def __init__(self, fileIndex = 0, filePath: str = DIRECTORY.FILE_PATH, radarName: str = DIRECTORY.RADAR_NAME, date: str =DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE, mode: str = DIRECTORY.MODE):
    if not DataManager.GRID_DATA:
      DataManager.GRID_DATA = DataManager.getAllDataFilePaths(filePath, radarName, date, "grid/" + mode)

    self.currentIndex = fileIndex
    self.getGrid()

  def getGrid(self):
    self.data = pyart.io.read_grid(DataManager.GRID_DATA[self.currentIndex])
    self.currentReflectivity = self.data.fields['reflectivity']['data']          

  def increaseIndex(self):
    self.currentIndex += 1

    if (self.currentIndex >= DataManager.NUM_OF_GRID_FILES):
      self.currentIndex = 0

  def readDataFromFilePath(self, filePath: str):
    self.data = pyart.io.read_grid(filePath)

  def readDataFromOtherMode(self, mode: str, fileIndex: int = 0):
    data = DataManager.getAllDataFilePaths(mode = "grid/" + mode)
    self.data = pyart.io.read_grid(data[fileIndex])

  def readDataFromOtherDate(self, date: str, mode: str, fileIndex: int = 0):
    data = DataManager.getAllDataFilePaths(date = date, mode="grid/" + mode)
    self.data = pyart.io.read_grid(data[fileIndex])

  def update(self, index = None):
    if index is not None:
      self.currentIndex = index
    else:
      self.increaseIndex()

    self.getGrid()

  def get_vertices_position(self, scaler):
    a = self.data.z['data']
    b = self.data.y['data']
    c = self.data.x['data']

    # Create all combinations of indices
    idx_a, idx_b, idx_c = np.meshgrid(np.arange(len(a)), np.arange(len(b)), np.arange(len(c)), indexing='ij')
    combinations = np.array([c[idx_c.ravel()], b[idx_b.ravel()], a[idx_a.ravel()]]).T
    return scaler.fit_transform(
        combinations
    )

  def get_all_vertices_by_threshold(self, threshold = 0):

    # indices = np.where(np.logical_and(np.logical_not(self.currentReflectivity.mask),self.currentReflectivity.data >= threshold))

    # storm Identification testing
    # grid_size = get_grid_size(self.data)
    # min_size = 4 / np.prod(grid_size[1:]/1000)
    # masked = self.data.fields['reflectivity']['data']
    # masked.data[masked.data == masked.fill_value] = 0
    # frame = get_filtered_frame(masked.data, min_size,
    #                            32)
    # indices = np.where(self.currentReflectivity > threshold)

    scaler = MinMaxScaler(feature_range=(-1.0, 1.0))
    vertices = self.get_vertices_position(scaler)
    return {
        'position': vertices[indices],
        'color': color(self.currentReflectivity[indices])
    }
