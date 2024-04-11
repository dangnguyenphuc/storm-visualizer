import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSlot, QFile, QTextStream
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
# from object3dBK import GLWidget
from Object3d import GLWidget
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from sidebar_ui import Ui_MainWindow
import sys
import numpy as np
from Radar import DataManager, DIRECTORY
from Config import SECOND, TICK
from Utils import folderEmpty

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

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setContentsMargins(0, 0, 0, 0)

        self.ui.icon_only_widget.hide()
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.home_btn_2.setChecked(True)
        self.zoom_factor = 0
        self.last_pos = None
        self.mouse_x = 0
        self.mouse_y = 0 
        self.initGL()
        self.initHomePage() 
        #! add item to drop down 3d
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

        # timers
        mainTimer = QtCore.QTimer(self)
        mainTimer.setInterval(int(TICK))   # period, in milliseconds
        mainTimer.timeout.connect(self.glWidget.updateGL)
        mainTimer.start()


        self.switchFrameTimer = QtCore.QTimer(self)
        self.switchFrameTimer.timeout.connect(self.goNextFile)
        self.switchFrameTimer.stop()

        self.errorTimer = QtCore.QTimer(self)
        self.errorTimer.setInterval(5 * SECOND) 
        self.errorTimer.timeout.connect(self.clearError)
        self.errorTimer.stop()
        # just change when value change
        self.ui.threshold.textChanged.connect(self.getThreshold)
        self.ui.timerInput.textChanged.connect(self.getSwichFrameTimer)
        self.ui.fileBox.currentIndexChanged.connect(self.getFile)
        self.ui.radarBox.currentIndexChanged.connect(self.getRadar)
        self.ui.modeBox.currentIndexChanged.connect(self.getMode)
        self.ui.dateBox.currentIndexChanged.connect(self.getDate)
        self.ui.clutterFilterToggle.stateChanged.connect(self.getClutterFilter)
        self.last_pos = None
        self.mouse_x = 0
        self.mouse_y = 0
        
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.last_pos is None:
            return
        dx = event.x() - self.last_pos.x()
        dy = event.y() - self.last_pos.y()
        if event.buttons() & Qt.LeftButton:
            self.glWidget.teapot_pos[0] += dx / self.width() * 10 # Convert to OpenGL coordinate
            self.glWidget.teapot_pos[1] -= dy / self.height() * 10 
            self.update()
        self.last_pos = event.pos()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_pos = None 
    def wheelEvent(self,event):
        """
        wheel event
        Args:
            event (QtGui.QWheelEvent): wheel event
        for user:
            mouse wheel clockwise (counter-clockwise) to zoom in (zoom out)
                scale ability: 0.25 -> 25
            held left mouse button to move object
        """
        if self.ui.stackedWidget.currentIndex() == 1:
            try:
                delta = event.angleDelta().y()
                self.zoom_factor += (delta and delta // abs(delta))
                if self.zoom_factor >= 96:
                    self.zoom_factor = 96
                elif self.zoom_factor <= -3:
                    self.zoom_factor = -3
                self.zoom = 1 + self.zoom_factor * 0.25
                if event.modifiers() & Qt.ControlModifier:
                    self.glWidget.zoom_center[0] += 0
                    self.glWidget.zoom_center[1] += 0
                else:
                    mouse_x = (event.x()   - 150) / self.glWidget.width() * 2 -  1
                    mouse_y = (event.y()   - 140 )/ self.glWidget.height()* 2 - 1
                    if event.angleDelta().y() > 0:
                        self.glWidget.zoom_center[0] += mouse_x/10
                        self.glWidget.zoom_center[1] += mouse_y/10
                    else: 
                        self.glWidget.zoom_center[0] -= mouse_x/10
                        self.glWidget.zoom_center[1] -= mouse_y/10
                self.update()
                self.glWidget.setUpScale(self.zoom)
            except:
                print("error")

    ## Function for searching
    def on_search_btn_clicked(self):
        self.ui.stackedWidget.setCurrentIndex(5)
        search_text = self.ui.search_input.text().strip()
        if search_text:
            self.ui.label_9.setText(search_text)

    ## Function for changing page to user page
    # def on_user_btn_clicked(self):
    #     self.ui.stackedWidget.setCurrentIndex(6)

    ## Change QPushButton Checkable status when stackedWidget index changed
    def on_stackedWidget_currentChanged(self, index):
        btn_list = self.ui.icon_only_widget.findChildren(QPushButton) \
                    + self.ui.full_menu_widget.findChildren(QPushButton)

        for btn in btn_list:
            if index in [5, 6]:
                btn.setAutoExclusive(False)
                btn.setChecked(False)
            else:
                btn.setAutoExclusive(True)

    ## functions for changing menu page
    def on_home_btn_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def on_home_btn_2_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def on_view3d_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def on_view3d_2_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def on_view2d_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(2)

    def on_view2d_2_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(2)

    def on_other_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(3)

    def on_other_2_toggled(self, ):
        self.ui.stackedWidget.setCurrentIndex(3)
#
#     def on_customers_btn_1_toggled(self):
#         self.ui.stackedWidget.setCurrentIndex(4)
#
#     def on_customers_btn_2_toggled(self):
#         self.ui.stackedWidget.setCurrentIndex(4)

    def addItemRadar(self):
        self.ui.radarBox.clear()

        for radar in DataManager.listAllRadar():
            self.ui.radarBox.addItem(radar)
        self.ui.radarBox.setCurrentIndex(DataManager.listAllRadar().index(DIRECTORY.RADAR_NAME[:-1]))

    def addItemDate(self):
        self.ui.dateBox.clear()
        try:
            for date in DataManager.listAllDateOfRadar(radar=DIRECTORY.RADAR_NAME):
                self.ui.dateBox.addItem(date)
            self.ui.dateBox.setCurrentIndex(DataManager.listAllDateOfRadar().index(DIRECTORY.YEAR + DIRECTORY.MONTH + DIRECTORY.DATE[:-1]))
        except Exception as ex:
            print(f"An error occurred: {ex}")


    def addItemFile(self):
        self.ui.fileBox.clear()
        for file in DataManager.listAllFile(DIRECTORY.FILE_PATH, DIRECTORY.RADAR_NAME, DIRECTORY.YEAR+DIRECTORY.MONTH+DIRECTORY.DATE, DIRECTORY.MODE):
            self.ui.fileBox.addItem(file)
        self.ui.fileBox.setCurrentIndex(0)


    def addItemMode(self):
        self.ui.modeBox.clear()
        for mode in DataManager.listAllModeOnDate():
            self.ui.modeBox.addItem(mode)
        self.ui.modeBox.setCurrentIndex(DataManager.listAllModeOnDate().index(DIRECTORY.MODE[:-1]))

    def getRadar(self, index = 0):
        #! get value of radar
        radar = self.ui.radarBox.currentText()
        if not folderEmpty(DIRECTORY.getCurrentPath(filename=True) + radar):
            DIRECTORY.RADAR_NAME = radar + "/"
            self.getDate()
        else:
            print(f"Radar {radar} is empty")
            self.ui.radarBox.setCurrentIndex(DataManager.listAllRadar().index(DIRECTORY.RADAR_NAME[:-1]))

    def getDate(self, index=0):
        #! get value of date
        year, month, date = self.ui.dateBox.currentText().split("/")

        if not folderEmpty(DIRECTORY.getCurrentPath(radar=True) + year):
            DIRECTORY.YEAR = year + "/"
            if not folderEmpty(DIRECTORY.getCurrentPath(year=True) + month):
                DIRECTORY.MONTH = month + "/"
                if not folderEmpty(DIRECTORY.getCurrentPath(month=True) + date):
                    DIRECTORY.DATE = date + "/"
                    self.getMode()
                else:
                    print(f"{DIRECTORY.RADAR_NAME} does not have {year}/{month}/{date}")
            else:
                print(f"{DIRECTORY.RADAR_NAME} does not have {month} in this {year}")
        else:
            print(f"{DIRECTORY.RADAR_NAME} does not have {year}")


    def getFile(self, index=0):
        self.glWidget.update(index=index, clutterFilter=self.ui.clutterFilterToggle.isChecked())
        self.glWidget.updateGL()

    def getMode(self, index=0):
        #! get value of mode
        if not folderEmpty(DIRECTORY.getCurrentPath(date=True)+self.ui.modeBox.currentText()):
            DIRECTORY.MODE = self.ui.modeBox.currentText() + "/"
            self.addItemFile()
            self.glWidget.resetRadar(filePath=DIRECTORY.FILE_PATH, radarName=DIRECTORY.RADAR_NAME, date=DIRECTORY.YEAR+DIRECTORY.MONTH+DIRECTORY.DATE, mode=DIRECTORY.MODE)
            self.getFile()
        else:
            print("This mode is empty")

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

    def getSwichFrameTimer(self):
        if self.ui.timerInput.text():
            if int(self.ui.timerInput.text()) > 0:
                self.switchFrameTimer.setInterval( int(self.ui.timerInput.text()) * SECOND)
                self.switchFrameTimer.start()
            else: self.switchFrameTimer.stop()
        else: self.switchFrameTimer.stop()

    def initGL(self):

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.glWidget = GLWidget(self)
        self.glWidget.setSizePolicy(sizePolicy)
        self.ui.scrollArea.setWidget(self.glWidget)
        
        self.ui.scrollArea.setWidgetResizable(True)
        self.ui.scrollArea.setAlignment(Qt.AlignHCenter)
        self.ui.scrollArea.setAlignment( Qt.AlignVCenter)

        self.ui.slider_3d_x.valueChanged.connect(self.updateSliderX)
        # self.ui.slider_3d_x.setMaximum(115)

        self.ui.slider_3d_y.valueChanged.connect(self.updateSliderY)
        # self.ui.slider_3d_y.setMaximum(115)

        self.ui.slider_3d_z.valueChanged.connect(self.updateSliderZ)
        # self.ui.slider_3d_z.setMaximum(115)

        self.ui.slider_3d_x.setMaximum(115)
        self.ui.slider_3d_y.setMaximum(115)
        self.ui.slider_3d_z.setMaximum(115)

        self.ui.preFile.clicked.connect(self.goPrevFile)
        self.ui.nextFile.clicked.connect(self.goNextFile)

        self.ui.resetView.clicked.connect(self.reset3DView)


    def reset3DView(self):
        """
        Reset 3D view
        """
        #reset zoome view
        self.glWidget.zoom_center[0] = 0
        self.glWidget.zoom_center[1] = 0
        
        # reset position
        self.glWidget.teapot_pos[0] = 0
        self.glWidget.teapot_pos[1] = 0

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
        self.ui.changeDirData.clicked.connect(lambda: self.chooseDir())

    def chooseDir(self):
        self.dataDir = QFileDialog.getExistingDirectory()
        self.ui.curData.setText(self.dataDir)
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

    def getSwichFrameTimer(self):
        if self.ui.timerInput.text():
            if int(self.ui.timerInput.text()) > 0:
                self.switchFrameTimer.setInterval( int(self.ui.timerInput.text()) * SECOND)
                self.switchFrameTimer.start()
            else: self.switchFrameTimer.stop()
        else: self.switchFrameTimer.stop()
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
    window.show()

    # Exit
    sys.exit(app.exec())
