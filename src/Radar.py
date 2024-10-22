import numpy as np
import os
import pickle
from matplotlib import pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from scipy import ndimage

import pyart
import wradlib as wrl
import xarray

from Titan.StormIdentification import getStormWithIndex, getStormCount
from Titan.tint.grid_utils import *
from Config import *
from Utils import listDirInDir, listFile, is_valid_day_for_month_year, getYearMonthDate, color

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
      self.grid_data = None
    else: 
      self.setData()
  
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

    if filePath is None:
      filePath = self.filePath
    if radarName is None:
      radarName = self.radarName
    if date is None:
      date = self.date
    if mode is None:
      mode = self.mode

    filePaths = [
        filePath + radarName + date + mode + fileName for fileName in self.listAllFile(filePath, radarName, date, mode)
    ]
    return filePaths

  def setGridData(self):
    self.grid_data = self.getAllDataFilePaths(mode="grid/" + self.mode)
  
  def setData(self):
    self.raw_data = self.getAllDataFilePaths()
    self.setGridData()
  
  def getTrackFileName(self):
    return self.year[-3:-1] + self.month[:-1] + self.day[:-1]

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

  def genGrid(self, params = DEFAULT_GRID_CONFIG):
    def get_grid(radar, grid_shape = (150, 401, 401), z_range = None, y_range = None, x_range = None, h_factor = 0., nb = 0.6, bsp = 1., min_radius = 200):
      
      if z_range is None:
        z_range = (0,radar.gate_z['data'][-1])
      if y_range is None:
        z_range = (-radar.gate_y['data'][-1], radar.gate_y['data'][-1])
      if x_range is None:
        x_range = (-radar.gate_x['data'][-1], radar.gate_x['data'][-1])

      """ Returns grid object from radar object. """
      grid = pyart.map.grid_from_radars(
          radar, grid_shape=grid_shape, 
          grid_limits=(z_range, y_range, x_range),
          fields=['reflectivity'], gridding_algo='map_gates_to_grid',
          h_factor=h_factor, nb=nb, bsp=bsp, min_radius=min_radius)
      return grid

    def write_grid():
        tmp_dir = self.filePath + self.radarName + self.date + "grid/" + self.mode
        if not os.path.exists(tmp_dir):
          os.makedirs(tmp_dir)
        else:
          # return if grids already created
          if len(listFile(tmp_dir)) == len(listFile(self.filePath + self.radarName + self.date + self.mode)):
            return

        keys = self.getAllDataFilePaths()
        for key in keys:
            radar = pyart.io.read(key)
            grid = get_grid(radar, params['grid_shape'], params['z_lims'], params['y_lims'], params['x_lims'], params['h_factor'], params['nb'], params['bsp'], params['min_radius'])
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
    self.tracksObj = None
    self.setTrackFile()
    self.isGrid = False
    self.stormCount = 0
    self.currentIndex = fileIndex
    self.getRadar()

  def setDataMangerWithParam(self, filePath = DEFAULT_FILE_PATH, radarName = DEFAULT_RADAR_NAME, year = DEFAULT_YEAR, month = DEFAULT_MONTH, day = DEFAULT_DATE, mode = DEFAULT_MODE):
    self.DataManager = DataManager(filePath=filePath, radarName=radarName, year=year, month=month, day=day, mode=mode)
  
  def setDataManger(self, DataManager: DataManager):
    self.DataManager = DataManager
  
  def setTrackFile(self):
    self.trackFile = "src/Titan/TrackingData/" + self.DataManager.getTrackFileName() + ".pkl"
    if not os.path.exists(self.trackFile):
      self.trackFile = None
      self.tracksObj = None
    else:
      self.loadTrackFile()
    
    
  def loadTrackFile(self):
    if self.trackFile is not None:
      with open(self.trackFile, 'rb') as file:
        self.tracksObj = pickle.load(file)
    
  def getRadar(self):

    self.data = pyart.io.read(self.DataManager.raw_data[self.currentIndex])
    try:
      self.gridData = pyart.io.read_grid(self.DataManager.grid_data[self.currentIndex])
    except:
      print("There are some errors with grid file!")
    # self.currentReflectivity = self.data.fields['reflectivity']['data'].flatten()

    if self.isGrid:
      self.currentReflectivity = self.gridData.fields['reflectivity']['data'].flatten()
      self.getStorm()
    else:
      self.currentReflectivity = self.data.fields['reflectivity']['data'].flatten()

    self.positions = self.get_vertices_position()
  
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

        plt.savefig('plot/pyart_ppi.png')
        plt.close()
        del display
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_polar":
        da.plot()
        plt.savefig('plot/wrl_polar.png')
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_ppi":
        da_geo.wrl.vis.plot(add_colorbar=True, vmax=70, vmin=20)
        plt.savefig('plot/wrl_ppi.png')
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_clutter":
        clutter.wrl.vis.plot(cmap=plt.cm.gray)
        plt.title("Clutter Map")
        plt.savefig('plot/wrl_clutter.png')
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_ppi_no_clutter":
        data_no_clutter.wrl.vis.plot(add_colorbar=True, vmin = 0)
        plt.savefig('plot/wrl_ppi_no_clutter.png')
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_attenuation_correction":
        '''https://docs.wradlib.org/en/latest/notebooks/basics/wradlib_workflow.html'''
        '''In this mode, we can plot'''
        pass
      elif mode == "wrl_plot_rain":
        depths.wrl.vis.plot()
        plt.savefig('plot/wrl_plot_rain.png')
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths
      elif mode == "wrl_plot_scan_strategy":
        wrl.vis.plot_scan_strategy(r, self.data.fixed_angle['data'], site)
        plt.savefig('plot/wrl_plot_scan_strategy.png')
        plt.close()
        del da, da_geo, clutter, pia, data_attcorr, z, R, depths

  def increaseIndex(self):
    self.currentIndex += 1

    if (self.currentIndex >= len(self.DataManager.raw_data)):
      self.currentIndex = 0

  def readDataFromFilePath(self, filePath: str):
    self.data = pyart.io.read(filePath)

  def update(self, index = None, isGrid = None):
    if index is not None:
      self.currentIndex = index
    # else:
    #   self.increaseIndex()

    if isGrid is not None:
      self.isGrid = isGrid

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

  def get_vertices_position(self):
    scaler = MinMaxScaler(feature_range=(-1.0, 1.0))
    if not self.isGrid:
      # if Raw format
      return scaler.fit_transform(
          np.column_stack(
              (
              self.data.gate_x["data"].flatten(),
              self.data.gate_y["data"].flatten(),
              self.data.gate_z["data"].flatten()
              )
          )
      )
    else:
      # if is Grid format
      a = self.gridData.z['data']
      b = self.gridData.y['data']
      c = self.gridData.x['data']

      # Create all combinations of indices
      idx_a, idx_b, idx_c = np.meshgrid(np.arange(len(a)), np.arange(len(b)), np.arange(len(c)), indexing='ij')
      combinations = np.array([c[idx_c.ravel()], b[idx_b.ravel()], a[idx_a.ravel()]]).T
      maxPoint = np.array([np.max(self.data.gate_x['data']), np.max(self.data.gate_y['data']), np.max(self.data.gate_z['data'])])
      appendPoints = np.array([
        maxPoint
      ])
      combinations = np.concatenate((combinations, appendPoints), axis=0)
      return scaler.fit_transform(
          combinations
      )[:-1]
  
  def getCurrentTracks(self):
    if self.tracksObj and self.currentIndex in self.tracksObj.tracks.index.levels[0]:
      return self.tracksObj.tracks.loc[self.currentIndex]
    else:
      return None
      
  def get_all_vertices_by_threshold(self, threshold = 0):
      indices = np.where(np.logical_and(np.logical_not(self.currentReflectivity.mask), self.currentReflectivity.data >= threshold))

      if self.isGrid:
        tracklines = {}
        if self.tracksObj and self.currentIndex in self.tracksObj.tracks.index.levels[0]:
          currentStormCenters = self.tracksObj.tracks.loc[self.currentIndex]

          # iterator
          for index, row in currentStormCenters.iterrows():
            center = [
              row.center[2],
              row.center[1],
              row.center[0]
            ]
            tracklines.setdefault(index, [center])
          
          # get all previous tracking objects
          currentIndex = max(self.currentIndex - 1, 0)
          if currentIndex != self.currentIndex:
            while currentIndex in self.tracksObj.tracks.index.levels[0]:
              for index, row in self.tracksObj.tracks.loc[currentIndex].iterrows():
                if index in tracklines:
                  centerPos = [
                    row.center[2],
                    row.center[1],
                    row.center[0]
                  ]
                
                  tracklines[index].insert(0, centerPos)
                # else:
                #   tracklines.setdefault(index, [centerPos])

              currentIndex -= 1
          if len(tracklines) == 0:
            print("There is no storm in this file.")
          else:
            scaler = MinMaxScaler(feature_range=(-1.0, 1.0))
            for key in tracklines:
              tracklines[key].append(
                [
                  self.gridData.x['data'].data[0], 
                  self.gridData.y['data'].data[0], 
                  self.gridData.z['data'].data[0]
                ])
              tracklines[key].append(
                [
                  np.max(self.data.gate_x['data']), 
                  np.max(self.data.gate_y['data']), 
                  np.max(self.data.gate_z['data'])
                ])
              tracklines[key] = scaler.fit_transform(tracklines[key])
              tracklines[key] = tracklines[key][:-2]
          return {
            'position': self.positions[indices],
            'color': color(self.currentReflectivity[indices]),
            'trackLines': tracklines
          } 
          

      return {
          'position': self.positions[indices],
          'color': color(self.currentReflectivity[indices]),
      }

  def get_all_vertices(self):
    r = self.currentReflectivity
    r.data[r.data == r.fill_value] = 0
    return {
          'position': self.positions,
          'color': color(r),
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

      temp = np.ma.masked_array(np.empty((0, self.data.ngates)), mask=np.empty((0, self.data.ngates), dtype=bool))
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
        temp = np.ma.concatenate((temp, masked_array), axis=0)

      self.currentReflectivity = temp.flatten()

    else:
      self.currentReflectivity = self.data.fields['reflectivity']['data'].flatten()
  
  def getStorm(self):
    if self.tracksObj.stormFrames.get(self.currentIndex) is not None:
      self.stormFrame = self.tracksObj.stormFrames[self.currentIndex]
      self.stormCount = getStormCount(self.stormFrame)
      if self.stormCount == 0:
        print("Error: There is no storm in this {}".format(self.currentIndex))
        return
  
  def getStormVertex(self, index = 1):
    if self.stormCount == 0:
      print("Error: There is no storm in file {} in folder".format(self.currentIndex, self.DataManager.getCurrentPath(mode=True)))
      return None, None

    if index > self.stormCount:
      print("Error: Invalid storm index")
      return None, None

    concatenated_array, plane = getStormWithIndex(self.gridData, self.stormFrame, index=index)
    scaler = MinMaxScaler(feature_range=(-1.0, 1.0))
    
    # append min and max point
    concatenated_array = np.concatenate((
      concatenated_array,
      np.array([
        [self.gridData.x['data'].data[0], self.gridData.y['data'].data[0], self.gridData.z['data'].data[0]],
        [np.max(self.data.gate_x['data']), np.max(self.data.gate_y['data']), np.max(self.data.gate_z['data'])]
      ])
    ), axis = 0)

    scaled_array = scaler.fit_transform(concatenated_array)
    
    # remove last 2 points
    scaled_array = scaled_array[:-2]

    edge_points = []
    for i in plane:
      edge_points.append(scaled_array[i[0]:i[1]])
    
    side_planes = []
    for i in range(len(edge_points) - 1):
      points = np.concatenate((edge_points[i], edge_points[i+1]), axis = 0)
      side_planes.append(points)
    return edge_points, side_planes
  
  def getAllStormVertices(self):
    edge_points = []
    side_planes = []
    for i in np.arange(self.stormCount) + 1:
      points, sides = self.getStormVertex(index=i)
      edge_points.append(points)
      side_planes.append(sides)
    
    return edge_points, side_planes