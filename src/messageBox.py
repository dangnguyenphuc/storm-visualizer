from PyQt5.QtWidgets import QMessageBox
from PyQt5 import  QtGui
import sys

def quitQuestionBox():
    msg =QMessageBox()
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/icon/icon/thunderstorm.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    msg.setWindowIcon(icon)
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
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/icon/icon/thunderstorm.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    msg.setWindowIcon(icon)
    msg.setIcon(QMessageBox.Critical)
    msg.setText(text)
    msg.styleSheet("Qlabel:{color:red}")
    msg.setWindowTitle("Titan: Something is wrong")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setDefaultButton(QMessageBox.Ok)
    msg.exec_()