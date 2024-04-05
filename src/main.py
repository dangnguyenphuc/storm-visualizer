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
from Config import *
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

        self.initGL()
        self.initHomePage()
        #! add item to drop down 3d
        self.addItemRadar()
        self.addItemDate()
        self.addItemMode()
        self.addItemFile()

        # validator
        thresholdValidator = QIntValidator()
        thresholdValidator.setRange(0, 100)  # For example, allow numbers from -1000 to 1000
        self.ui.threshold.setValidator(thresholdValidator)

        # timers
        mainTimer = QtCore.QTimer(self)
        mainTimer.setInterval(int(TICK))   # period, in milliseconds
        mainTimer.timeout.connect(self.glWidget.updateGL)
        mainTimer.start()

        # just change when value change
        self.ui.threshold.textChanged.connect(self.getThreshold)
        self.ui.fileBox.currentIndexChanged.connect(self.getFile)
        self.ui.radarBox.currentIndexChanged.connect(self.getRadar)
        self.ui.modeBox.currentIndexChanged.connect(self.getMode)
        self.ui.dateBox.currentIndexChanged.connect(self.getDate)



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
        self.glWidget.update(index=index)
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

    def getIsGrid(self):
        self.isGrid = self.ui.IsGrid.isChecked()  # -> bool

    def getThreshold(self):
        if self.ui.threshold.text():
            self.glWidget.update(threshold=int(self.ui.threshold.text()))
        else:
            self.glWidget.update(threshold=0)

        self.glWidget.updateGL()

    def initGL(self):
        # if not bool(glGenBuffers):
        #     print("glGenBuffers not available")
        #     return
        self.glWidget = GLWidget(self)
        self.ui.horizontalLayout_8.insertWidget(0,self.glWidget)


        self.ui.slider_3d_x.valueChanged.connect(self.updateSliderX)
        # self.ui.slider_3d_x.setMaximum(115)

        self.ui.slider_3d_y.valueChanged.connect(self.updateSliderY)
        # self.ui.slider_3d_y.setMaximum(115)

        self.ui.slider_3d_z.valueChanged.connect(self.updateSliderZ)
        # self.ui.slider_3d_z.setMaximum(115)

        self.ui.slider_3d_x.setMaximum(115)
        self.ui.slider_3d_y.setMaximum(115)
        self.ui.slider_3d_z.setMaximum(115)

        self.ui.preFile.clicked.connect(lambda: self.goPrevFile())
        self.ui.nextFile.clicked.connect(lambda: self.goNextFile())

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