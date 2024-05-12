TICK = 10 # must smaller than 1000
SECOND = 1000 # in ms

DEFAULT_FILE_PATH = "../Data/"
DEFAULT_RADAR_NAME = "NHB/"
DEFAULT_YEAR = "2023/"
DEFAULT_MONTH = "06/"
DEFAULT_DATE = "01/"
DEFAULT_MODE = "1_prt/"

DEFAULT_2D_TRACK_CONFIG = {
  'FIELD_THRESH': 32,
  'MIN_SIZE': 8,
  'SEARCH_MARGIN': 4000,
  'FLOW_MARGIN': 10000,
  'MAX_FLOW_MAG': 50,
  'MAX_DISPARITY': 999,
  'MAX_SHIFT_DISP': 15,
  'ISO_THRESH': 8,
  'ISO_SMOOTH': 3,
  'GS_ALT': 1500
}

DEFAULT_3D_TRACK_CONFIG = {
  'FIELD_THRESH': 32,
  'MIN_SIZE': 8,
  'SEARCH_MARGIN': 4000,
  'FLOW_MARGIN': 10000,
  'MAX_FLOW_MAG': 50,
  'MAX_DISPARITY': 999,
  'MAX_SHIFT_DISP': 15,
  'ISO_THRESH': 8,
  'ISO_SMOOTH': 3,
}

DEFAULT_PULL_DATA_CONFIG = {  
  'startTime': "2024-04-24 00:00:00",
  'endTime' : "2024-04-24 23:59:59",
  'archiveMode': False,
  'sleepSecs' : 10,
  'dryRun' : False,
  'force'  : False,
  'tmpDir' : "../Temp" ,
  'outputDir': "../Data",
}
