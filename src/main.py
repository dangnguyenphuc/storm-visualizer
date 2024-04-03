import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton
from PyQt5.QtCore import pyqtSlot, QFile, QTextStream
from Object3d import GLWidget
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from sidebar_ui import Ui_MainWindow
import sys




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

        self.ui.icon_only_widget.hide()
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.home_btn_2.setChecked(True)
        self.initGL()
        timer = QtCore.QTimer(self)
        timer.setInterval(10)   # period, in milliseconds
        timer.timeout.connect(self.glWidget.updateGL)
        timer.start()
    ## Function for searching
    def on_search_btn_clicked(self):
        self.ui.stackedWidget.setCurrentIndex(5)
        search_text = self.ui.search_input.text().strip()
        if search_text:
            self.ui.label_9.setText(search_text)

    ## Function for changing page to user page
    def on_user_btn_clicked(self):
        self.ui.stackedWidget.setCurrentIndex(6)

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

    def on_dashborad_btn_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def on_dashborad_btn_2_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def on_orders_btn_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(2)

    def on_orders_btn_2_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(2)

    def on_products_btn_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(3)

    def on_products_btn_2_toggled(self, ):
        self.ui.stackedWidget.setCurrentIndex(3)

    def on_customers_btn_1_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(4)

    def on_customers_btn_2_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(4)

    def initGL(self):
        self.ui.verticalLayout_6.removeWidget(self.ui.openGLWidget)
        # self.ui.gridLayout_3.removeWidget(self.ui.label_5)
        self.glWidget = GLWidget(self)
        self.ui.verticalLayout_6.insertWidget(0, self.glWidget)

        self.ui.horizontalSlider.valueChanged.connect(lambda val: self.glWidget.setRotX(val))

        self.ui.horizontalSlider_2.valueChanged.connect(lambda val: self.glWidget.setRotY(val))

        self.ui.horizontalSlider_3.valueChanged.connect(lambda val: self.glWidget.setRotZ(val))


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
    loadStyle(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())