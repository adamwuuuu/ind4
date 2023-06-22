#coding:UTF-8
import os,sys
from PyQt5 import QtWidgets,QtGui,QtCore
from controller.presentater import Controller





if __name__=="__main__":
    app = QtWidgets.QApplication(sys.argv)

    app.setStyle('Fusion')
    # pixmap = QtGui.QPixmap("Loading_icon.gif")
    # splash = QtWidgets.QSplashScreen(pixmap)
    # splash.showMessage("讀取中....")
    # splash.show()
    # app.processEvents()
    #
    # splash.close()
    ex = Controller()
    sys.exit(app.exec_())