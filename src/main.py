import sys
import numpy as np

import PyQt5
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import QFile, QTextStream, Qt
from PyQt5.QtGui import QIntValidator, QPixmap

from Object3d import GLWidget
from Frontend import Ui_MainWindow
from Radar import DataManager
from Utils import folderEmpty, getHourMinuteSecond
from Config import SECOND, TICK
from messageBox import quitQuestionBox, errorBox

# Set high DPI scaling attributes
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

class MainWindow(QMainWindow):
    """
    DashBoard contains side bar.
    We implement behaviors of dashboard here.

    Args:
        QMainWindow (QWidget): Main widget
    """
    def __init__(self):
        super(MainWindow, self).__init__()

        self.DataManager = DataManager()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setContentsMargins(0, 0, 0, 0)

        self.ui.icon_only_widget.hide()
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.home_btn_2.setChecked(True)
        self.ui.exit_btn_1.disconnect()
        self.ui.exit_btn_2.disconnect()
        self.ui.exit_btn_2.clicked.connect(quitQuestionBox)
        self.ui.exit_btn_1.clicked.connect(quitQuestionBox)
        self.zoom_factor = 0
        self.last_pos = None
        self.mouse_x = 0
        self.mouse_y = 0

        # init OpenGL Widget
        self.initGL()
        # init HomePage
        self.initHomePage() 
        # init 2D Page
        self.init2DView() 
        # init Pro view
        self.initProView()

        # add item for drop down
        self.addItemRadar()
        self.addItemDate()
        self.addItemMode()
        self.addItemFile()

        # validator
        thresholdValidator = QIntValidator()
        thresholdValidator.setRange(0, 100)
        timerValidator = QIntValidator()
        timerValidator.setRange(0, 3600)
        self.ui.threshold.setValidator(thresholdValidator)
        self.ui.threshold.setText(str(self.glWidget.threshold))
        self.ui.timerInput.setValidator(timerValidator)
        self.ui.timerInput.setText("0")

        self.ui.threshold_pro.setValidator(thresholdValidator)
        self.ui.threshold_pro.setText(str(self.glWidget.threshold))
        self.ui.timerInput_pro.setValidator(timerValidator)
        self.ui.timerInput_pro.setText("0")

        # timers
        mainTimer = PyQt5.QtCore.QTimer(self)
        mainTimer.setInterval(int(TICK))   # period, in milliseconds
        mainTimer.timeout.connect(self.glWidget.updateGL)
        mainTimer.start()

        self.switchFrameTimer = PyQt5.QtCore.QTimer(self)
        self.switchFrameTimer.timeout.connect(self.goNextFile)
        self.switchFrameTimer.stop()

        self.errorTimer = PyQt5.QtCore.QTimer(self)
        self.errorTimer.setInterval(5 * SECOND) 
        self.errorTimer.timeout.connect(self.clearError)
        self.errorTimer.stop()

        # just change when value change
        self.ui.page_2.showEvent = lambda event: self.page2Connect(event)
        self.ui.page_2.hideEvent = lambda event: self.page2Disconnect(event)
        self.page_2Connected = False


    def closeEvent(self, event):
        if quitQuestionBox() == QMessageBox.Cancel:
            event.ignore()
        else:
            event.accept()

    def page2Connect(self, event):
      if not self.page_2Connected:
        self.ui.threshold.textChanged.connect(self.getThreshold)
        self.ui.timerInput.textChanged.connect(self.getSwichFrameTimer)
        self.ui.threshold_pro.textChanged.connect(self.getThresholdPro)
        self.ui.timerInput_pro.textChanged.connect(self.getSwichFrameTimerPro)
        self.ui.fileBox.currentIndexChanged.connect(self.getFile)
        self.ui.radarBox.currentIndexChanged.connect(self.getRadar)
        self.ui.modeBox.currentIndexChanged.connect(self.getMode)
        self.ui.dateBox.currentIndexChanged.connect(self.getDate)
        self.ui.clutterFilterToggle.stateChanged.connect(self.getClutterFilter)
        self.page_2Connected = True
      
    def page2Disconnect(self, event):
      if self.page_2Connected:
        self.ui.threshold.textChanged.disconnect(self.getThreshold)
        self.ui.timerInput.textChanged.disconnect(self.getSwichFrameTimer)
        self.ui.radarBox.currentIndexChanged.disconnect(self.getRadar)
        self.ui.modeBox.currentIndexChanged.disconnect(self.getMode)
        self.ui.dateBox.currentIndexChanged.disconnect(self.getDate)
        self.ui.fileBox.currentIndexChanged.disconnect(self.getFile)
        self.ui.clutterFilterToggle.stateChanged.disconnect(self.getClutterFilter)
        self.page_2Connected = False

    def keyPressEvent(self, event):
        if event.key()== PyQt5.QtCore.Qt.Key_4:
            self.ui.other_1.setChecked(True)
            self.ui.other_2.setChecked(True)
        elif event.key()== PyQt5.QtCore.Qt.Key_3:
            self.ui.view3d_1.setChecked(True)
            self.ui.view3d_2.setChecked(True)
        elif event.key()== PyQt5.QtCore.Qt.Key_2:
            self.ui.view2d_1.setChecked(True)
            self.ui.view2d_2.setChecked(True)
        elif event.key()== PyQt5.QtCore.Qt.Key_1:
            self.ui.home_btn_1.setChecked(True)
            self.ui.home_btn_1.setChecked(True)
        elif event.key()== PyQt5.QtCore.Qt.Key_Escape:
            quitQuestionBox()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        mousePos = event.pos()
        if event.button() == Qt.LeftButton and self.glWidget.rect().contains(mousePos):
            self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.last_pos is not None :
          dx = event.x() - self.last_pos.x()
          dy = event.y() - self.last_pos.y()
          if event.buttons() & Qt.LeftButton :
              self.glWidget.mousePos[0] += dx / self.width() * 10 # Convert to OpenGL coordinate
              self.glWidget.mousePos[1] -= dy / self.height() * 10 
              self.update()
          self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton  and self.glWidget.rect().contains(event.pos()):
            self.last_pos = None 

    def wheelEvent(self, event):
        """
        wheel event
        Args:
            event (QtGui.QWheelEvent): wheel event
        for user:
            mouse wheel clockwise (counter-clockwise) to zoom in (zoom out)
                scale ability: 0.25 -> 25
            held left mouse button to move object
        """
        mousePos = event.pos()
        if (self.ui.stackedWidget_2.currentIndex() == 0 or self.ui.stackedWidget_2.currentIndex() == 2 ) and self.glWidget.rect().contains(mousePos):
            try:
                delta = event.angleDelta().y()
                self.zoom_factor += (delta and delta // abs(delta))
                if self.zoom_factor >= 96:
                    self.zoom_factor = 96
                elif self.zoom_factor <= -3:
                    self.zoom_factor = -3
                zoom = 1 + self.zoom_factor * 0.25
                if event.modifiers() & Qt.AltModifier:
                    self.glWidget.zoom_center[0] += 0
                    self.glWidget.zoom_center[1] += 0
                else:
                    mouse_x = (event.x() - 150) / self.glWidget.width() * 2 -  1
                    mouse_y = (event.y() - 140 )/ self.glWidget.height()* 2 - 1
                    if event.angleDelta().y() > 0:
                        self.glWidget.zoom_center[0] += mouse_x/10
                        self.glWidget.zoom_center[1] += mouse_y/10
                    else: 
                        self.glWidget.zoom_center[0] -= mouse_x/10
                        self.glWidget.zoom_center[1] -= mouse_y/10
                self.update()
                self.glWidget.setUpScale(zoom)
            except:
                print("error")
        else:
            event.ignore()

    # Function for searching
    def on_search_btn_clicked(self):
        self.ui.stackedWidget.setCurrentIndex(5)
        search_text = self.ui.search_input.text().strip()
        if search_text:
            self.ui.label_9.setText(search_text)

    # Change QPushButton Checkable status when stackedWidget index changed
    def on_stackedWidget_currentChanged(self, index):
        btn_list = self.ui.icon_only_widget.findChildren(QPushButton) \
                    + self.ui.full_menu_widget.findChildren(QPushButton)

        for btn in btn_list:
            if index in [5, 6]:
                btn.setAutoExclusive(False)
                btn.setChecked(False)
            else:
                btn.setAutoExclusive(True)

    def on_home_btn_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.labelPage.setText("Home Page")

    def on_home_btn_2_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.labelPage.setText("Home Page")


    def on_view3d_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_2.setCurrentIndex(0)
        self.ui.labelPage.setText("3D View")
        self.ui.slider_3d_x.setEnabled(True)
        self.ui.slider_3d_y.setEnabled(True)

    def on_view3d_2_toggled(self):
        self.ui.scrollArea_4.takeWidget()
        self.ui.scrollArea.setWidget(self.glWidget)
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_2.setCurrentIndex(0)
        self.ui.labelPage.setText("3D View")
        self.ui.slider_3d_x.setEnabled(True)
        self.ui.slider_3d_y.setEnabled(True)

    def on_view2d_1_toggled(self):
        self.ui.scrollArea_4.takeWidget()
        self.ui.scrollArea.setWidget(self.glWidget)
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_2.setCurrentIndex(1)
        self.ui.labelPage.setText("2D View")

        # self.ui.slider_3d_x.setDisabled(True)
        # self.ui.slider_3d_y.setDisabled(True)

    def on_view2d_2_toggled(self):
        self.ui.scrollArea.takeWidget()
        self.ui.scrollArea_4.setWidget(self.glWidget)
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_2.setCurrentIndex(1)
        self.ui.labelPage.setText("2D View")

        self.ui.slider_3d_x.setDisabled(True)
        self.ui.slider_3d_y.setDisabled(True)

    def on_other_1_toggled(self):
        self.ui.scrollArea.takeWidget()
        self.ui.scrollArea_4.setWidget(self.glWidget)

        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_2.setCurrentIndex(2)
        self.ui.labelPage.setText("Pro View")


    def on_other_2_toggled(self, ):
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.stackedWidget_2.setCurrentIndex(2)
        self.ui.labelPage.setText("Pro View")

#
#     def on_customers_btn_1_toggled(self):
#         self.ui.stackedWidget.setCurrentIndex(4)
#
#     def on_customers_btn_2_toggled(self):
#         self.ui.stackedWidget.setCurrentIndex(4)

    def addItemRadar(self):
        radars = self.DataManager.listAllRadar()
        self.ui.radarBox.clear()
        for radar in radars:
            self.ui.radarBox.addItem(radar)
        if len(radars) > 0:
          try:
            nhabeIndex = radars.index("NHB")
          except:
            nhabeIndex = radars.index("nha-be-radar")
          self.DataManager.radarName = radars[nhabeIndex] + "/"
          index = self.ui.radarBox.findText("NHB", PyQt5.QtCore.Qt.MatchFixedString)
          if index >= 0:
              self.ui.radarBox.setCurrentIndex(index)
          else:
              index = self.ui.radarBox.findText("nha-be-radar", PyQt5.QtCore.Qt.MatchFixedString)
              self.ui.radarBox.setCurrentIndex(index)

    def addItemDate(self):
        self.ui.dateBox.clear()
        try:
            dates =  self.DataManager.listAllDateOfRadar()
            for date in dates:
                self.ui.dateBox.addItem(date)
            if len(dates) > 0:
              self.DataManager.date = dates[0] + "/"
              self.DataManager.year, self.DataManager.month, self.DataManager.day = dates[0].split("/")
              self.DataManager.year += "/"
              self.DataManager.month += "/"
              self.DataManager.day += "/"

              self.ui.dateBox.setCurrentIndex(0)
        except Exception as ex:
            print(f"An error occurred: {ex}")

    def addItemMode(self):
        self.ui.modeBox.clear()

        modes = self.DataManager.listAllModeOnDate()
        for mode in modes:
            self.ui.modeBox.addItem(mode)
        if len(modes) > 0:
          self.DataManager.mode = modes[0] + "/"
          self.ui.modeBox.setCurrentIndex(0)

    def addItemFile(self):
        self.ui.fileBox.clear()
        files = self.DataManager.listAllFile()
        for file in files:
            self.ui.fileBox.addItem(file)
        if len(files) > 0:
          self.DataManager.raw_data = self.DataManager.getAllDataFilePaths()
          self.ui.fileBox.setCurrentIndex(0)


          

    def getRadar(self, index = 0):
        #! get value of radar
        radar = self.ui.radarBox.currentText()
        if radar != "" and not folderEmpty(self.DataManager.getCurrentPath(filename=True) + radar):
            self.DataManager.radarName = radar + "/"
            self.clearPage2Box(date = True)
            self.addItemDate()
            self.getDate()
        else:
            print(f"Radar {radar} is empty")
            index = self.ui.radarBox.findText("NHB", QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.ui.radarBox.setCurrentIndex(index)
            else:
                index = self.ui.radarBox.findText("nha-be-radar", QtCore.Qt.MatchFixedString)
                self.ui.radarBox.setCurrentIndex(index)

    def getDate(self, index=0):
        #! get value of date
        date = self.ui.dateBox.currentText()
        if date != "":
          year, month, day = date.split("/")
          if not folderEmpty(self.DataManager.getCurrentPath(radar=True) + year):
              self.DataManager.year = year + "/"
              if not folderEmpty(self.DataManager.getCurrentPath(year=True) + month):
                  self.DataManager.month = month + "/"
                  if not folderEmpty(self.DataManager.getCurrentPath(month=True) + day):
                      self.DataManager.day = day + "/"
                      self.clearPage2Box(mode = True)
                      self.DataManager.setDate()
                      self.addItemMode()
                      self.getMode()
                  else:
                      print(f"{self.DataManager.radarName} does not have {year}/{month}/{day}")
              else:
                  print(f"{self.DataManager.radarName} does not have {month} in this {year}")
          else:
              print(f"{self.DataManager.radarName} does not have {year}")

    def getMode(self, index=0):
        #! get value of mode
        mode = self.ui.modeBox.currentText()
        if mode != "" and not folderEmpty(self.DataManager.getCurrentPath(date=True) + mode):
            self.DataManager.mode = mode + "/"
            self.clearPage2Box(files = True)
            self.addItemFile()
            self.glWidget.resetRadar(DataManager=self.DataManager)
            self.getFile()
        else:
            print(f"{mode} mode is empty")

    def getFile(self, index=0):
      f = self.ui.fileBox.currentText()
      if f != "":
        self.glWidget.update(index=index, clutterFilter=self.ui.clutterFilterToggle.isChecked())
        self.glWidget.updateGL()
        self.addInfor()
        self.addExtraInfor()
        self.addStormList()
        self.ui.lat_pro.setText(str(self.glWidget.radar.data.longitude['data'][0]))
        self.ui.long_pro.setText(str(self.glWidget.radar.data.latitude['data'][0]))
        

    def getClutterFilter(self, state):
        if state:
            self.glWidget.update(clutterFilter=True)
        else:
            self.glWidget.update(clutterFilter=False)
        self.glWidget.updateGL()

    def getThreshold(self):
        if self.ui.threshold.text():
            print("Filter threshold with value: " + self.ui.threshold.text())
            self.glWidget.update(threshold=int(self.ui.threshold.text()))
        else:
            self.glWidget.update(threshold=0)
        self.glWidget.updateGL()
    def getThresholdPro(self):
        if self.ui.threshold_pro.text():
            print("Filter threshold with value: " + self.ui.threshold_pro.text())
            self.glWidget.update(threshold=int(self.ui.threshold_pro.text()))
        else:
            self.glWidget.update(threshold=0)
        self.glWidget.updateGL()
    def getSwichFrameTimer(self):
        if self.ui.timerInput.text():
            if int(self.ui.timerInput.text()) > 0:
                self.switchFrameTimer.setInterval( int(self.ui.timerInput.text()) * SECOND)
                self.switchFrameTimer.start()
            else: self.switchFrameTimer.stop()
        else:
          self.ui.timerInput.setText("0")
          self.switchFrameTimer.stop()
    def getSwichFrameTimerPro(self):
        if self.ui.timerInput_pro.text():
            if int(self.ui.timerInput_pro.text()) > 0:
                self.switchFrameTimer.setInterval( int(self.ui.timerInput_pro.text()) * SECOND)
                self.switchFrameTimer.start()
            else: self.switchFrameTimer.stop()
        else:
          self.ui.timerInput_pro.setText("0")
          self.switchFrameTimer.stop()

    #write a fuction init 2d view add image to label: ui.view_2d_label
    def init2DView(self): 
      '''create mode box for user choosing mode'''
    #   self.glWidget.radar.plot(mode="wrl_plot_scan_strategy", sweep=1)
      # pixmap = QPixmap('temp.jpg')
      # self.ui.view_2d_label.setPixmap(pixmap)
      # self.ui.view_2d_label.setScaledContents(True)
      # self.addPlotBoxMode()
      # self.addPlotModeImage()
      pass

    def initGL(self):

        sizePolicy = PyQt5.QtWidgets.QSizePolicy(PyQt5.QtWidgets.QSizePolicy.Expanding, PyQt5.QtWidgets.QSizePolicy.Expanding)

        # ''' specified GL version: core 330 '''
        # glformat = PyQt5.QtOpenGL.QGLFormat()
        # glformat.setVersion(3, 3)
        # glformat.setProfile(PyQt5.QtOpenGL.QGLFormat.CoreProfile)

        self.glWidget = GLWidget(self)
        

        self.glWidget.setSizePolicy(sizePolicy)
        self.ui.scrollArea.setWidget(self.glWidget)
        
        self.ui.scrollArea.setWidgetResizable(True)
        self.ui.scrollArea.setAlignment(Qt.AlignHCenter)
        self.ui.scrollArea.setAlignment( Qt.AlignVCenter)

        self.ui.slider_3d_x.valueChanged.connect(self.updateSliderX)
        self.ui.slider_3d_y.valueChanged.connect(self.updateSliderY)
        self.ui.slider_3d_z.valueChanged.connect(self.updateSliderZ)

        self.ui.slider_3d_x.setMaximum(115)
        self.ui.slider_3d_y.setMaximum(115)
        self.ui.slider_3d_z.setMaximum(115)

        self.ui.preFile.clicked.connect(self.goPrevFile)
        self.ui.nextFile.clicked.connect(self.goNextFile)

        self.ui.resetView.clicked.connect(self.reset3DView)

    def initProView(self):
        self.ui.scrollArea_4.setMinimumHeight(int(self.ui.stackedWidget_2.height() * 0.5))
        self.ui.scrollArea_4.setMinimumWidth(int(self.ui.page_3.width() * 0.75))
        self.ui.label2d_pro.setMinimumWidth(int(self.ui.page_3.width() * 0.25))
        self.ui.scrollArea.setWidget(self.glWidget)

        # 2D 
        source = ['temp.jpg']
        scanStrategyImage = QPixmap(source)
        self.ui.label2d_pro.setPixmap(scanStrategyImage)
        self.ui.label2d_pro.setScaledContents(True)

        self.ui.slider_pro_x.valueChanged.connect(self.updateSliderX)
        self.ui.slider_pro_y.valueChanged.connect(self.updateSliderY)
        self.ui.slider_pro_z.valueChanged.connect(self.updateSliderZ)

        self.ui.slider_pro_x.setMaximum(115)
        self.ui.slider_pro_y.setMaximum(115)
        self.ui.slider_pro_z.setMaximum(115)

        self.ui.resetView_pro.clicked.connect(self.reset3DView)

        self.addInfor()
        self.addExtraInfor()
        self.addStormList()
        self.ui.lat_pro.setText(str(self.glWidget.radar.data.longitude['data'][0]))
        self.ui.long_pro.setText(str(self.glWidget.radar.data.latitude['data'][0]))

    def addPlotBoxMode(self):
        plotMode = ["pyart_ppi","wrl_polar","wrl_ppi", "wrl_clutter", "wrl_ppi_no_clutter", "wrl_attenuation_correction","wrl_plot_rain", "wrl_plot_scan_strategy", ]
        # for i in range(0, len(plotMode)):
        #     self.ui.plot_mode_box.addItem(plotMode[i])
        self.ui.plot_mode_box.addItems(plotMode)
        self.ui.plot_mode_box.setCurrentIndex(0)

    def addPlotModeImage(self):
        source = 'placeholder.png'
        pixmap = QPixmap(source)
        pixmap = pixmap.scaled(int(self.ui.scrollArea_3.width() *0.5),int(self.ui.scrollArea_3.width() *0.5), Qt.KeepAspectRatio)
        self.ui.pyart_ppi.setPixmap(pixmap)
        self.ui.wrl_polar.setPixmap(pixmap)
        self.ui.wrl_ppi.setPixmap(pixmap)
        self.ui.wrl_clutter.setPixmap(pixmap)
        self.ui.wrl_ppi_no_clutter.setPixmap(pixmap)
        self.ui.wrl_attenuation_correction.setPixmap(pixmap)
        self.ui.wrl_plot_rain.setPixmap(pixmap)
        self.ui.wrl_plot_scan_strategy.setPixmap(pixmap)

        # self.ui.pyart_ppi.setScaledContents(True)   
        # self.ui.wrl_polar.setScaledContents(True)
        # self.ui.wrl_ppi.setScaledContents(True)
        # self.ui.wrl_clutter.setScaledContents(True)
        # self.ui.wrl_ppi_no_clutter.setScaledContents(True)
        # self.ui.wrl_attenuation_correction.setScaledContents(True)
        # self.ui.wrl_plot_rain.setScaledContents(True)
        # self.ui.wrl_plot_scan_strategy.setScaledContents(True)
        

    def getPlotMode(self) -> str:
        return self.ui.plot_mode_box.currentText()

    def addInfor(self):
        self.ui.otherIn4_pro.clear()
        time = getHourMinuteSecond(self.glWidget.radar.data)
        currentTime = f'{time[0]}:{time[1]}:{time[2]}'
        entries = [
          'This is other information box',
          f'Radar: {self.DataManager.radarName}', 
          f"Altitude: {self.glWidget.radar.data.altitude['data'][0]}",
          f"Time: {currentTime}",
          f"Ray Missing: {self.glWidget.radar.data.metadata['rays_missing']}"
        ]
        self.ui.otherIn4_pro.addItems(entries)

    def addExtraInfor(self):
        self.ui.extraInfo_pro.clear()
        entries = ['This is extra information box',f'Radar: {self.DataManager.radarName}', 'two', 'three']
        self.ui.extraInfo_pro.addItems(entries)

    def addStormList(self):
        self.ui.stromList.clear()
        entries = [f'storm 1: theshold...', 'storm 1: theshold...', 'storm 1: theshold...']
        self.ui.stromList.addItems(entries)
        self.ui.stromList.setCurrentIndex(-1)

    def reset3DView(self):
        """
        Reset 3D view
        """
        #reset zoome view
        self.glWidget.zoom_center[0] = 0
        self.glWidget.zoom_center[1] = 0
        
        # reset position
        self.glWidget.mousePos[0] = 0
        self.glWidget.mousePos[1] = 0
        self.updateSliderX(0)
        self.updateSliderY(0)
        self.updateSliderZ(0)
        # seset scale
        self.update()
        self.glWidget.setUpScale(1)
    def goPrevFile(self):
        index = max(0, self.ui.fileBox.currentIndex()-1)
        self.ui.fileBox.setCurrentIndex(index)
        self.getFile(index=index)


    def goNextFile(self):
        index = min(self.ui.fileBox.count() - 1,self.ui.fileBox.currentIndex()+1)
        self.ui.fileBox.setCurrentIndex(index)
        self.getFile(index=index)

    def updateSliderX(self, val):
        self.glWidget.setRotX(val)
        tmp_value = val * np.pi
        tmp_value = min(tmp_value, 360)
        self.ui.x_value.setText(str(int(tmp_value)) + "°")


    def updateSliderY(self, val):
        self.glWidget.setRotY(val)
        tmp_value = val * np.pi
        tmp_value = min(tmp_value, 360)
        self.ui.y_value.setText(str(int(tmp_value)) + "°")

    def updateSliderZ(self, val):
        self.glWidget.setRotZ(val)
        tmp_value = val * np.pi
        tmp_value = min(tmp_value, 360)
        self.ui.z_value.setText(str(int(tmp_value)) + "°")

    def initHomePage(self):
        self.ui.changeDirData.clicked.connect(self.chooseDir)
        self.ui.actionOpen_Folder.triggered.connect(self.chooseDir)

    def chooseDir(self):
      dataDir = QFileDialog.getExistingDirectory()
      if dataDir is not None and dataDir != "":
        self.DataManager.reconstructFile(dataDir)
        self.DataManager.clearAll()
        self.ui.curData.setText(dataDir)
        self.DataManager.filePath = dataDir
        if self.DataManager.filePath[-1] != "/": 
          self.DataManager.filePath += "/"
        self.addItemRadar()
        self.addItemDate()
        self.addItemMode()
        self.addItemFile()

    def getError(self, err):
        """
        show error message
        call this function when error occurs to display error message
        Args:
            err (str): error message"""
        self.ui.errorBox.setText(err)
        self.errorTimer.start()

    def clearError(self):
        self.ui.errorBox.clear()
        self.errorTimer.stop()

    def clearPage2Box(self, radarName = False, date = False, mode = False, files = False):
      if radarName:
        self.ui.radarBox.clear()
      elif date:
        self.ui.dateBox.clear()
        self.ui.modeBox.clear()
        self.ui.fileBox.clear()
      elif mode:
        self.ui.modeBox.clear()
        self.ui.fileBox.clear()
      elif files:
        self.ui.fileBox.clear()
    
def loadStyle(QApplication):
    """
    load style file for application
    Args:
        QApplication (QtGui.QGuiApplication): our application
    """
    style_file = QFile("./style/style.qss")
    style_file.open(QFile.ReadOnly | QFile.Text)
    style_stream = QTextStream(style_file)
    QApplication.setStyleSheet(style_stream.readAll())

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load style
    loadStyle(app)

    # Window Constructor
    window = MainWindow()

    # Window run
    window.showMaximized()

    # Exit
    sys.exit(app.exec())
