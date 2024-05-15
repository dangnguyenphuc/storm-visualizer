import sys
import time
import os
import datetime
from datetime import timedelta

import urllib
from xml.dom import minidom
from sys import stdin
from urllib.request import urlopen
import subprocess
from subprocess import call

import pyart

from PyQt5.QtCore import QThread, pyqtSignal
from Config import DEFAULT_PULL_DATA_CONFIG

def getNodeText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


def runCommand(cmd):
    
    try:
        retcode = subprocess.call(cmd, shell=True)
        if retcode < 0:
            print("Child was terminated by signal: ", -retcode, file=sys.stderr)
        else:
            print("Child returned code: ", retcode, file=sys.stderr)
    except OSError as e:
        print >>sys.stderr, "Execution failed:", e

class PullDataWorkerThread(QThread):
    """
    Worker thread class.
    """
    # Define a signal to communicate with the main thread
    update_signal = pyqtSignal(str)
    doneSignal = pyqtSignal()

    def __init__(self, DataManager, params = None, ):
        super().__init__()
        if params is None:
          self.params = DEFAULT_PULL_DATA_CONFIG
        else:
          self.params = params
        
        self.DataManager = DataManager

    def run(self):
        self.fileCount = 0
        self.thisScriptName = os.path.basename(__file__)
        
        # initialize
        
        beginString = "BEGIN: " + self.thisScriptName
        nowTime = datetime.datetime.now()
        beginString += " at " + str(nowTime)
        self.update_signal.emit(beginString)

        if not self.params['archiveMode']:
          lookbackSecs = timedelta(0, 1800)
          while(True):
              self.fileCount = 0
              nowTime = time.gmtime()
              endTime = datetime.datetime(nowTime.tm_year, nowTime.tm_mon, nowTime.tm_mday,
                                          nowTime.tm_hour, nowTime.tm_min, nowTime.tm_sec)
              startTime = endTime - lookbackSecs
              self.manageRetrieval(startTime, endTime)
              time.sleep(self.params['sleepSecs'])
          self.update_signal.emit("Done")
          time.sleep(1)
          self.doneSignal.emit()
          return

        self.manageRetrieval()
                
        endString = "END: " + self.thisScriptName
        nowTime = datetime.datetime.now()
        endString += " at " + str(nowTime)

        self.update_signal.emit(endString)
        time.sleep(1)
        self.doneSignal.emit()

    def manageRetrieval(self, startTime = None, endTime = None):
        if startTime is None:
          startTime = self.params['startTime']
        if endTime is None:
          endTime = self.params['endTime']

        startTime = datetime.datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
        endTime = datetime.datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S")


        if (startTime.day == endTime.day):

            # single day
            startDay = datetime.date(startTime.year, startTime.month, startTime.day)
            self.getForInterval(startDay, startTime, endTime)
            print("---->> Num files downloaded: ", self.fileCount, file=sys.stderr)
            return

        # multiple days

        tdiff = endTime - startTime
        tdiffSecs = tdiff.total_seconds()

        startDay = datetime.date(startTime.year, startTime.month, startTime.day)
        endDay = datetime.date(endTime.year, endTime.month, endTime.day)
        thisDay = startDay
        while (thisDay <= endDay):

            if (thisDay == startDay):
                # get to end of start day
                periodStart = startTime
                periodEnd = datetime.datetime(thisDay.year, thisDay.month, thisDay.day,
                                              23, 59, 59)
                self.getForInterval(thisDay, periodStart, periodEnd)

            elif (thisDay == endDay):
                # get from start of end day
                periodStart = datetime.datetime(thisDay.year, thisDay.month, thisDay.day,
                                                0, 0, 0)
                periodEnd = endTime
                self.getForInterval(thisDay, periodStart, periodEnd)

            else:
                # get for the full day
                periodStart = datetime.datetime(thisDay.year, thisDay.month, thisDay.day,
                                                0, 0, 0)
                periodEnd = datetime.datetime(thisDay.year, thisDay.month, thisDay.day,
                                              23, 59, 59)
                self.getForInterval(thisDay, periodStart, periodEnd)

            # go to next day
            thisDay = thisDay + timedelta(1)

        print("---->> Num files downloaded: ", self.fileCount, file=sys.stderr)

    def getForInterval(self, thisDay, startTime, endTime):

        # get the local file list, i.e. files already downloaded

        localFileList = self.getLocalFileList(thisDay)

        # construct the URL

        awsDateStr =  startTime.strftime("%Y/%m/%d")
        bucketURL = "http://noaa-nexrad-level2.s3.amazonaws.com"
        dirListURL = bucketURL+ "/?prefix=" + awsDateStr + "/" + self.params['radarName']

        # get the listing in XML

        xmldoc = minidom.parse(urlopen(dirListURL))
        itemlist = xmldoc.getElementsByTagName('Key')

        for x in itemlist:
            # Only process files that look like "2012/07/02/KJAX/KJAX20120702_030836_V06.gz"
            fileEntry = str(getNodeText(x.childNodes))
            try:
                (fyear, fmonth, fday, rname, fileName) = str.split(fileEntry, '/')
                year = int(fileName[4:8]);
                month = int(fileName[8:10]);
                day = int(fileName[10:12]);
                hour = int(fileName[13:15]);
                minute = int(fileName[15:17]);
                sec = int(fileName[17:19]);
                fileTime = datetime.datetime(year, month, day, hour, minute, sec);
            except:
                continue

            if(fileTime >= startTime and fileTime <= endTime):
                if (self.params['force']):
                    self.doDownload(fileTime, fileEntry, fileName)
                else:
                    if (fileName not in localFileList):
                        self.doDownload(fileTime, fileEntry, fileName)

    ########################################################################
    # Download specified file
    def doDownload(self, fileTime, fileEntry, fileName):

        if(self.params['dryRun']):
            # no download
            return

        # download into tmp file

        dataURL = "https://noaa-nexrad-level2.s3.amazonaws.com"
        tmpPath = os.path.join(self.params['tmpDir'], fileName)
        try:
            tmpFile = open(tmpPath, 'wb')
            urlPath = os.path.join(dataURL, fileEntry);
            myfile = urllib.request.urlopen(urlPath)
            tmpFile.write(myfile.read())
            tmpFile.close()
            self.fileCount = self.fileCount + 1
        except OSError as e:
            print("ERROR: Got error: ", e, file=sys.stderr)

        # create final dir
        dateStr =  fileTime.strftime("%Y/%m/%d/fixed/")
        radarDir = os.path.join(self.DataManager.filePath, self.params['radarName'])
        outDayDir = os.path.join(radarDir, dateStr)
        try:
            os.makedirs(outDayDir)
        except OSError as exc:
            print("WARNING: trying to create dir: ", outDayDir, file=sys.stderr)
            print("Exception: ", exc, file=sys.stderr)
        
        # move to output dir
        
        cmd = "mv " + tmpPath + " " + outDayDir
        runCommand(cmd)

        # write latest_data_info
        
        timeStr = fileTime.strftime("%Y%m%d%H%M%S")
        relPath = os.path.join(dateStr, fileName)
        cmd = "LdataWriter -dir " + radarDir \
              + " -rpath " + relPath \
              + " -ltime " + timeStr \
              + " -writer " + self.thisScriptName \
              + " -dtype level2"
        runCommand(cmd)

    ########################################################################
    # Get list of files already downloaded

    def getLocalFileList(self, date):

        # make the target directory and go there
        
        dateStr = date.strftime("%Y/%m/%d/fixed/")
        radarDir = os.path.join(self.DataManager.filePath, self.params['radarName'])
        dayDir = os.path.join(radarDir, dateStr)
        try:
            os.makedirs(dayDir)
        except OSError as exc:
            print("WARNING: trying to create dir: ", dayDir, file = sys.stderr)
            print("  exception: ", exc, file = sys.stderr)

        # get local file list - i.e. those which have already been downloaded

        # os.chdir(dayDir)
        localFileList = os.listdir(dayDir)
        localFileList.reverse()

        print("==>> localFileList: ", localFileList, file=sys.stderr)

        return localFileList
                
    ########################################################################
