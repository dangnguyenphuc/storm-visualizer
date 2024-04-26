import numpy as np
import os
from matplotlib import pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from scipy import ndimage

import pyart
import wradlib as wrl
import xarray

from tint.grid_utils import *
from Config import *
from Utils import listDirInDir, listFile, is_valid_day_for_month_year, color, getYearMonthDate

class DataManager:

  def __init__(self, filePath: str = DEFAULT_FILE_PATH, radarName: str = DEFAULT_RADAR_NAME, year: str = DEFAULT_YEAR, month: str = DEFAULT_MONTH, day: str = DEFAULT_DATE, mode: str = DEFAULT_MODE):
    if filePath is not None and filePath[-1] != "/": filePath += "/"
    if radarName is not None and radarName[-1] != "/": radarName += "/"
    if year is not None and year[-1] != "/": year += "/"
    if month is not None and month[-1] != "/": month += "/"
    if day is not None and day[-1] != "/": day += "/"
    if mode is not None and mode[-1] != "/": mode += "/"
    
    self.filePath = filePath
    self.radarName = radarName

    self.year = year
    self.month = month
    self.day = day

    self.setDate()
    self.mode = mode

    if self.filePath is None or self.radarName is None or self.date is None or self.mode is None:
      self.raw_data = None
    else: self.raw_data = self.getAllDataFilePaths()
  
  def setDate(self):
    if self.year is None or self.month is None or self.day is None:
      self.date = None
    else:
      self.date = self.year + self.month + self.day

  def clearAll(self):
    self.filePath = None
    self.radarName = None
    self.year = None
    self.month = None
    self.day = None
    self.date = None
    self.mode = None
    self.raw_data = None

  def getAllDataFilePaths(self, filePath = None, radarName = None, date = None, mode = None):

    if filePath is None and radarName is None and date is None and mode is None:
      filePath = self.filePath
      radarName = self.radarName
      date = self.date
      mode = self.mode

    filePaths = [
        filePath + radarName + date + mode + fileName for fileName in self.listAllFile(filePath, radarName, date, mode)
    ]
    return filePaths

  def reconstructFile(self, filePath = None):
    if filePath is None:
      filePath = self.filePath

    def loopThroughFiles(files):
      loopPath = []
      for f in files:
        try:
          radar = pyart.io.read(filePath + f)
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
          os.rename(filePath + f, path + f)
        except:
          continue
      for path in loopPath:
        self.splitData(filePath=path["filePath"], radarName=path["radarName"], date=path["date"], mode="")

    try:
      if filePath[-1] != '/': filePath += '/'
      folder = listDirInDir(filePath)
      if len(folder) > 0:
        currentFolder = folder[0]
        i = 0
        while len(folder):
          for item in os.listdir(filePath + currentFolder):
            os.rename(filePath + currentFolder + "/" + item, filePath + item + str(i))

          os.rmdir(filePath + currentFolder)
          folder = listDirInDir(filePath)
          i += 1
          if len(folder) > 0:
            currentFolder = folder[0]
          else: 
            print(f'{filePath} is empty.')
            break

      files = listFile(filePath)
      if len(files):
        loopThroughFiles(files=files)
    except Exception as e:
      print(e)

  def splitData(self, filePath = None, radarName = None, date = None, mode = None):

    if filePath is None and radarName is None and date is None and mode is None:
      filePath = self.filePath
      radarName = self.radarName
      date = self.date
      mode = self.mode
      

    if mode == "raw/" or not mode or mode == "":
      data = self.getAllDataFilePaths(filePath, radarName, date, mode)
      fixed = []
      dual = []
      staggered = []
      other = []

      for i in range(len(data)):
        radar = pyart.io.read(data[i])
        try:
          if radar.instrument_parameters['prt_mode']['data'][0].decode() == 'fixed' or len(radar.instrument_parameters['prt_mode']['data']) == 0:
            fixed.append(data[i])
          elif radar.instrument_parameters['prt_mode']['data'][0].decode() == 'dual' : dual.append(data[i])
          elif radar.instrument_parameters['prt_mode']['data'][0].decode() == 'staggered' : staggered.append(data[i])
          else: other.append(data[i])
        except:
          continue

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

  def genNhaBeRadarGrid(self):
    def get_grid(radar):
      """ Returns grid object from radar object. """
      grid = pyart.map.grid_from_radars(
          radar, grid_shape=(41, 801, 801), 
          grid_limits=((0, 20000), (-200000,200000), (-200000, 200000)),
          fields=['reflectivity'], gridding_algo='map_gates_to_grid',
          h_factor=0., nb=0.6, bsp=1., min_radius=200.)
      return grid

    def write_grid():
        tmp_dir = self.filePath + self.radarName + self.date + "grid/" + self.mode
        if not os.path.exists(tmp_dir):
          os.makedirs(tmp_dir)

        keys = self.getAllDataFilePaths()
        for key in keys:
            radar = pyart.io.read(key)
            grid = get_grid(radar)
            pyart.io.write_grid(tmp_dir + 'grid_' + key.split("/")[-1].split(".")[0] + '.nc', grid)
            del radar, grid

    write_grid()

  def listAllRadar(self):
    return listDirInDir(self.filePath)

  def listAllDateOfRadar(self):
    years = [year for year in listDirInDir(self.filePath + self.radarName) if year.isdigit()]
    if len(years) == 0:
      return None

    months = []
    for year in years:
      months += [year + "/" + month for month in listDirInDir(self.filePath + self.radarName + year) if month.isdigit() and int(month) <= 12 and int(month) > 0]
    if len(months) == 0:
      return None

    dates = []
    for month in months:
      dates += [month + "/" + date for date in listDirInDir(self.filePath + self.radarName + month) if date.isdigit() and is_valid_day_for_month_year(date, month)]
    if len(dates) == 0:
      return None

    return dates

  def listAllModeOnDate(self):
    mode = listDirInDir(self.filePath + self.radarName + self.date)
    # remove grid folder
    if "grid" in mode:
      mode.remove("grid")
    return mode

  def listAllFile(self, filePath = None, radarName = None, date = None, mode = None):

    if filePath is None and radarName is None and date is None and mode is None:
      filePath = self.filePath
      radarName = self.radarName
      date = self.date
      mode = self.mode

    return listFile(filePath + radarName + date + mode)

  def getCurrentPath(self, filename = False, radar = False, year = False, month = False, date = False, mode = False):
    if filename:
      return self.filePath

    if radar:
      return self.filePath + self.radarName

    if year:
      return self.filePath + self.radarName + self.year

    if month:
      return self.filePath + self.radarName + self.year + self.month

    if date:
      return self.filePath + self.radarName + self.date

    if mode:
      return self.filePath + self.radarName + self.date + self.mode

class Radar:

  def __init__(self, fileIndex: int = 0, filePath = DEFAULT_FILE_PATH, radarName = DEFAULT_RADAR_NAME, year = DEFAULT_YEAR, month = DEFAULT_MONTH, day = DEFAULT_DATE, mode = DEFAULT_MODE):
    self.setDataMangerWithParam(filePath = filePath, radarName = radarName, year = year, month = month, day = day, mode = mode)

    self.currentIndex = fileIndex
    self.getRadar()

  def setDataMangerWithParam(self, filePath = DEFAULT_FILE_PATH, radarName = DEFAULT_RADAR_NAME, year = DEFAULT_YEAR, month = DEFAULT_MONTH, day = DEFAULT_DATE, mode = DEFAULT_MODE):
    self.DataManager = DataManager(filePath=filePath, radarName=radarName, year=year, month=month, day=day, mode=mode)
  
  def setDataManger(self, DataManager: DataManager):
    self.DataManager = DataManager

  def getRadar(self):
    self.data = pyart.io.read(self.DataManager.raw_data[self.currentIndex])
    self.currentReflectivity = self.data.fields['reflectivity']['data'].flatten()
  
  def plot(self, mode = "wrl_ppi", sweep = 0):
      fig = plt.figure(figsize=(10, 7))
      plt.clf()


      data = np.ma.filled(self.data.fields['reflectivity']['data'], fill_value=-327)
      data = data[self.data.get_start(sweep) : self.data.get_end(sweep) + 1]
      phi = self.data.get_azimuth(sweep)
      theta = self.data.get_elevation(sweep)
      site = (self.data.longitude['data'][0], self.data.latitude['data'][0], self.data.altitude['data'][0])
      r = self.data.range['data']

      da = wrl.georef.create_xarray_dataarray(
            data = data,
            phi = phi,
            theta = theta,
            r=r,
            sweep_mode="azimuth_surveillance",
            site=site
      )

      da_geo = da.wrl.georef.georeference()
      clutter = da_geo.wrl.classify.filter_gabella(tr1=12, n_p=6, tr2=1.1)
      data_no_clutter = da_geo.wrl.ipol.interpolate_polar(clutter)
      pia = data_no_clutter.wrl.atten.correct_attenuation_constrained(
          a_max=1.67e-4,
          a_min=2.33e-5,
          n_a=100,
          b_max=0.7,
          b_min=0.65,
          n_b=6,
          gate_length=1.0,
          constraints=[wrl.atten.constraint_dbz, wrl.atten.constraint_pia],
          constraint_args=[[59.0], [20.0]],
      )
      data_attcorr = data_no_clutter + pia
      z = data_attcorr.wrl.trafo.idecibel()
      R = z.wrl.zr.z_to_r()
      depths = R.wrl.trafo.r_to_depth(300)
      

      if mode == "pyart_ppi":
        display = pyart.graph.RadarMapDisplay(self.data)
        display.plot_ppi_map('reflectivity',
                        resolution='50m',
                        sweep=sweep,
                        fig=fig,
                        lat_lines=np.arange(self.data.latitude['data'][0]-1.5, self.data.latitude['data'][0]+1.5, 1),
                        lon_lines=np.arange(self.data.longitude['data'][0]-1.5, self.data.longitude['data'][0]+1.5, 1),
                        min_lon=self.data.longitude['data'][0]-2.5,
                        max_lon=self.data.longitude['data'][0]+2.5,
                        min_lat=self.data.latitude['data'][0]-2.5,
                        max_lat=self.data.latitude['data'][0]+2.5,
                        lon_0=self.data.longitude['data'][0],
                        lat_0=self.data.latitude['data'][0])

        plt.savefig('plot/pyart_ppi.png', bbox_inches='tight', pad_inches=0)
        plt.close()
        del display
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_polar":
        da.plot()
        plt.savefig('plot/wrl_polar.png', bbox_inches='tight', pad_inches=0)
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_ppi":
        da_geo.wrl.vis.plot(add_colorbar=True)
        plt.savefig('plot/wrl_ppi.png', bbox_inches='tight', pad_inches=0)
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_clutter":
        clutter.wrl.vis.plot(cmap=plt.cm.gray)
        plt.title("Clutter Map")
        plt.savefig('plot/wrl_clutter.png', bbox_inches='tight', pad_inches=0)
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_ppi_no_clutter":
        data_no_clutter.wrl.vis.plot(add_colorbar=True, vmin = 0)
        plt.savefig('plot/wrl_ppi_no_clutter.png', bbox_inches='tight', pad_inches=0)
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_attenuation_correction":
        '''https://docs.wradlib.org/en/latest/notebooks/basics/wradlib_workflow.html'''
        '''In this mode, we can plot'''
        pass
      elif mode == "wrl_plot_rain":
        depths.wrl.vis.plot()
        plt.savefig('plot/wrl_plot_rain.png', bbox_inches='tight', pad_inches=0)
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_plot_scan_strategy":
        wrl.vis.plot_scan_strategy(r, self.data.fixed_angle['data'], site)
        plt.savefig('plot/wrl_plot_scan_strategy.png', bbox_inches='tight', pad_inches=0)
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths

        
      

  def increaseIndex(self):
    self.currentIndex += 1

    if (self.currentIndex >= len(self.DataManager.raw_data)):
      self.currentIndex = 0

  def readDataFromFilePath(self, filePath: str):
    self.data = pyart.io.read(filePath)

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

  def __init__(self, fileIndex: int = 0, filePath = DEFAULT_FILE_PATH, radarName = DEFAULT_RADAR_NAME, year = DEFAULT_YEAR, month = DEFAULT_MONTH, day = DEFAULT_DATE, mode = DEFAULT_MODE):
    self.setDataMangerWithParam(filePath = filePath, radarName = radarName, year = year, month = month, day = day, mode = mode)

    self.currentIndex = fileIndex
    self.getGrid()
  
  def setDataMangerWithParam(self, filePath = DEFAULT_FILE_PATH, radarName = DEFAULT_RADAR_NAME, year = DEFAULT_YEAR, month = DEFAULT_MONTH, day = DEFAULT_DATE, mode = DEFAULT_MODE):
    self.DataManager = DataManager(filePath=filePath, radarName=radarName, year=year, month=month, day=day, mode= "grid/" + mode)
  
  def setDataManger(self, DataManager: DataManager):
    self.DataManager = DataManager

  def getGrid(self):
    self.data = pyart.io.read_grid(self.DataManager.raw_data[self.currentIndex])
    self.currentReflectivity = self.data.fields['reflectivity']['data']

  def increaseIndex(self):
    self.currentIndex += 1

    if (self.currentIndex >= len(self.DataManager.raw_data)):
      self.currentIndex = 0

  def readDataFromFilePath(self, filePath: str):
    self.data = pyart.io.read_grid(filePath)

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
    def getSizeTable(frame):
      flat_image = pd.Series(frame.flatten())
      flat_image = flat_image[flat_image > 0]
      size_table = flat_image.value_counts(sort=False)
      return size_table

    masked = self.data.fields['reflectivity']['data']
    masked.data[masked.data == masked.fill_value] = 0
    masked.data[masked.data < 32] = 0

    frame, count = ndimage.label(masked.data)

    size_table = getSizeTable(frame)

    # determine smallObject 
    small_objects = size_table.keys()[size_table < 10]

    for obj in small_objects:
        frame[frame == obj] = 0
    
    # get unique value 
    self.currentReflectivity = frame.flatten()

    # self.currentReflectivity = self.data.fields['reflectivity']['data'].flatten()
    indices = np.where(self.currentReflectivity > threshold)
    scaler = MinMaxScaler(feature_range=(-10.0, 10.0))
    vertices = self.get_vertices_position(scaler)
    return {
        'position': vertices[indices],
        'color': color(self.currentReflectivity[indices])
    }
