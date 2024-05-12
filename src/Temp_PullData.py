from __future__ import print_function

import os
import sys
import time
import datetime
from datetime import timedelta

import string
import subprocess

import urllib
from xml.dom import minidom
from sys import stdin
from urllib.request import urlopen
from subprocess import call

import pyart

def main():

    # input
    global radarName
    global force
    global dryRun
    global sleepSecs


    global tmpDir, outputDir
    global startTime, endTime
    global archiveMode
    global fileCount

    startTime = datetime.datetime(2024, 4, 24, 0, 0, 0)   # NGÀY GIỜ
    endTime = datetime.datetime(2024, 4, 24, 23, 59, 59)  # NGÀY GIỜ
    archiveMode = False  # TOGGLE
    sleepSecs = 10   # INPUT MẶC ĐỊNH LÀ 10
    dryRun = False  # TOGGLE
    force = False   # TOGGLE
    tmpDir = "../Temp"    # KHỎI ĐỂ CÁI NÀY TRÊN PAGE CŨNG ĐƯỢC, ĐỠ XỬ LÝ
    outputDir = "../Data" # OUTDIR SẼ LÀ CÁI DIR LÚC ĐẦU MÀ MÌNH CHO TỤI NÓ CHỌN DATA DIR
    radarName = "KTLX" # CÁI NÀY LÀ 1 CÁI LIST ĐỂ LIST RADAR

    # initialize file count

    fileCount = 0

    global thisScriptName
    thisScriptName = os.path.basename(__file__)
    
    # initialize
    
    beginString = "BEGIN: " + thisScriptName
    nowTime = datetime.datetime.now()
    beginString += " at " + str(nowTime)

    if not archiveMode:
      lookbackSecs = timedelta(0, 1800)
      while(True):
          fileCount = 0
          nowTime = time.gmtime()
          endTime = datetime.datetime(nowTime.tm_year, nowTime.tm_mon, nowTime.tm_mday,
                                      nowTime.tm_hour, nowTime.tm_min, nowTime.tm_sec)
          startTime = endTime - lookbackSecs
          manageRetrieval(startTime, endTime)
          time.sleep(sleepSecs)
      return

    manageRetrieval(startTime, endTime)
            
    endString = "END: " + thisScriptName
    nowTime = datetime.datetime.now()
    endString += " at " + str(nowTime)
    

    sys.exit(0)

def manageRetrieval(startTime, endTime):

    if (startTime.day == endTime.day):

        # single day
        startDay = datetime.date(startTime.year, startTime.month, startTime.day)
        getForInterval(radarName, startDay, startTime, endTime)
        print("---->> Num files downloaded: ", fileCount, file=sys.stderr)
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
            getForInterval(radarName, thisDay, periodStart, periodEnd)

        elif (thisDay == endDay):
            # get from start of end day
            periodStart = datetime.datetime(thisDay.year, thisDay.month, thisDay.day,
                                            0, 0, 0)
            periodEnd = endTime
            getForInterval(radarName, thisDay, periodStart, periodEnd)

        else:
            # get for the full day
            periodStart = datetime.datetime(thisDay.year, thisDay.month, thisDay.day,
                                            0, 0, 0)
            periodEnd = datetime.datetime(thisDay.year, thisDay.month, thisDay.day,
                                          23, 59, 59)
            getForInterval(radarName, thisDay, periodStart, periodEnd)

        # go to next day
        thisDay = thisDay + timedelta(1)

    print("---->> Num files downloaded: ", fileCount, file=sys.stderr)

def getForInterval(radarName, thisDay, startTime, endTime):

    # get the local file list, i.e. files already downloaded

    localFileList = getLocalFileList(thisDay, radarName)

    # construct the URL

    awsDateStr =  startTime.strftime("%Y/%m/%d")
    bucketURL = "http://noaa-nexrad-level2.s3.amazonaws.com"
    dirListURL = bucketURL+ "/?prefix=" + awsDateStr + "/" + radarName

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
            if (force):
                doDownload(radarName, fileTime, fileEntry, fileName)
            else:
                if (fileName not in localFileList):
                    doDownload(radarName, fileTime, fileEntry, fileName)


def getNodeText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


########################################################################
# Download specified file
def doDownload(radarName, fileTime, fileEntry, fileName):

    global fileCount

    if(dryRun):
        # no download
        return

    # download into tmp file

    dataURL = "https://noaa-nexrad-level2.s3.amazonaws.com"
    tmpPath = os.path.join(tmpDir, fileName)
    try:
        tmpFile = open(tmpPath, 'wb')
        urlPath = os.path.join(dataURL,fileEntry);
        myfile = urllib.request.urlopen(urlPath)
        tmpFile.write(myfile.read())
        tmpFile.close()
        fileCount = fileCount + 1
    except OSError as e:
        print("ERROR: Got error: ", e, file=sys.stderr)

    # create final dir
    dateStr =  fileTime.strftime("%Y/%m/%d/fixed/")
    radarDir = os.path.join(outputDir, radarName)
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
          + " -writer " + thisScriptName \
          + " -dtype level2"
    runCommand(cmd)

########################################################################
# Get list of files already downloaded

def getLocalFileList(date, radarName):

    # make the target directory and go there
    
    dateStr = date.strftime("%Y/%m/%d/fixed/")
    radarDir = os.path.join(outputDir, radarName)
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

def runCommand(cmd):
    
    try:
        retcode = subprocess.call(cmd, shell=True)
        if retcode < 0:
            print("Child was terminated by signal: ", -retcode, file=sys.stderr)
        else:
            print("Child returned code: ", retcode, file=sys.stderr)
    except OSError as e:
        print >>sys.stderr, "Execution failed:", e

########################################################################
# kick off main method

if __name__ == "__main__":

   main()
