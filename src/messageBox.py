from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSlot, QFile, QTextStream
import sys
def quitQuestionBox():
    msg =QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText("Are you sure you want to quit?\nThe unsaved actions can not be restored.")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    msg.setDefaultButton(QMessageBox.Cancel)
    msg.setWindowTitle("Quit Titan")
    reply = msg.exec_()
    if reply == QMessageBox.Yes:
        sys.exit()
        
    return reply

# create a error box with str input
def errorBox(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(text)
    msg.styleSheet("Qlabel:{color:red}")
    msg.setWindowTitle("Titan: Something is wrong")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setDefaultButton(QMessageBox.Ok)
    msg.exec_()