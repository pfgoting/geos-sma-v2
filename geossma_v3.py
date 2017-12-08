# -*- coding: utf-8 -*-
# Author: cloud / Prince Garnett F. Goting
# Form implementation generated from reading ui file 'geossma_v3.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from PyQt4 import *
import sys,inspect
import os, time, datetime as dt
import shutil
import pandas as pd
import threading
import psutil
from distutils.dir_util import copy_tree
import numpy as np
import linecache

# Global paths
fpath = os.path.dirname(os.path.realpath(__file__))
resourcePath = os.path.join(fpath,'resources')
csvpath = os.path.join(resourcePath,'UBC97.csv')
rootPath = os.path.dirname(fpath)
rawDataPath = os.path.join(rootPath,'rawData')
histPath = os.path.join(fpath, 'archive')
print rootPath
out = r"\computed_parms\out"

# Plotting
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class MyPopup(QtGui.QDialog):
    def __init__(self, parent=None):
        super(MyPopup, self).__init__(parent)
        QtGui.QDialog.__init__(self,parent)

        # a figure instance to plot on
        self.figure = plt.figure(figsize=(20,14))

        # this is the Canvas Widget that displays the `figure`

        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # self.button = QtGui.QPushButton('Plot')
        

        # set the layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        # layout.addWidget(self.button)
        self.setLayout(layout)

class MonitorThread(QtCore.QThread):
    data_downloaded = QtCore.pyqtSignal(object)
    def __init__(self,inp,opt):
        QtCore.QThread.__init__(self)
        # self.threshold = threshold
        self.inp = inp
        self.opt = opt

    # App Functions
    def getFloorThreshold(self,sn):
        self.sn = sn
        self.thresholdDf = pd.read_csv(csvpath)
        self.snfile = pd.read_csv(os.path.join(resourcePath,"SN.csv"))
        self.flr = self.snfile.loc[self.snfile['S/N']==self.sn]

        self.ordinal = ordinal = lambda n: "%d%s" % (n,"tsnrhtdd".upper()[(n/10%10!=1)*(n%10<4)*n%10::4])
        # self.floor = ordinal(int(self.file.split('.')[1].split('_')[1][1:]))
        self.floor = ordinal(int(self.flr.FLOOR))
        print "{} floor selected...".format(self.floor)
        # Get threshold on floor
        self.floorDf = self.thresholdDf.loc[self.thresholdDf['STORY LEVEL'].str.match("{}".format(self.floor))==True]
        # self.floorDf = self.thresholdDf.loc[self.thresholdDf['STORY LEVEL'].str.contains("{}".format(self.floor))==True]
        self.xThreshold = (float(self.floorDf['DISPLACEMENT EQX (mm)'])/10.)*.7
        self.yThreshold = (float(self.floorDf['DISPLACEMENT EQY (mm)'])/10.)*.7
        self.zThreshold = (float(self.floorDf['DISPLACEMENT EQX (mm)'])/10.)*0.666*.7
        self.threshold = (self.xThreshold,self.yThreshold,self.zThreshold)
        return self.threshold

    def run(self):
        # Monitor changes in rawData folder
        self.path_to_watch = rawDataPath
        self.before = dict ([(self.f, None) for self.f in os.listdir(self.path_to_watch) if '.evt' in self.f])
        print self.before
        state = True
        self.added_group = []

        def func():
            # print "group: {}".format(self.added_group)
            self.valX = []
            self.valY = []
            self.valZ = []
            for self.added in self.added_group:
                aa = self.added
                print 'added: {}'.format(self.added)
                # Convert new files using k2cosmos
                print "converting: {}".format(self.added)
                self.sn = self.k2cosmos(self.added)
                time.sleep(5)

                # print 'Floor: {}'.format(self.added[0].split('.')[1].split('_')[1][1:])
                # Get floor threshold
                self.threshold = self.getFloorThreshold(self.sn)
                print "threshold: {}".format(self.threshold)

                # Run prism for new files
                # self.m0,self.m1,self.m2 = self.runPrism(self.threshold,self.inp,self.opt)
                # print "m0,m1,m2: {},{},{}".format(self.m0,self.m1,self.m2)
                self.vals = self.runPrism(self.opt)
                # if self.vals[0][0] >= self.valX:
                #     self.valX = self.vals[0][0]
                # elif self.vals[1][0] >= self.valY:
                #     self.valY = self.vals[0][0]
                # elif self.vals[2][0] >= self.valZ:
                #     self.valZ = self.vals[0][0]
                try:
                    self.valX.append(self.vals[0][0])
                except Exception as e:
                    self.valX.append(0.0)

                try:
                    self.valY.append(self.vals[1][0])
                except Exception as e:
                    self.valY.append(0.0)

                try:
                    self.valZ.append(self.vals[2][0])
                except Exception as e:
                    self.valZ.append(0.0)

                # archive output
                self.archiveOut = os.path.join(histPath,'computed_parms\out')
                copy_tree(self.outPath,self.archiveOut)

            self.vals = [(max(self.valX), 'X'), (max(self.valY), 'Y'), (max(self.valZ), 'Z')]
            self.m0,self.m1,self.m2 = self.checkThreshold(self.inp, self.vals, self.threshold)
            self.data_downloaded.emit((self.m0,self.m1,self.m2))
            time.sleep(0.1)
            self.added_group = []
        while state:
            time.sleep (3)
            self.after = dict ([(self.f, None) for self.f in os.listdir(self.path_to_watch) if '.evt' in self.f])
            self.added = [self.f for self.f in self.after if not self.f in self.before]
            self.removed = [self.f for self.f in self.before if not self.f in self.after]

            if self.added:
                print "Added: ", ", ".join(self.added)
                self.timeNow = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print "A new event has been recorded at {}.".format(self.timeNow)
                self.added_group.extend(self.added)
                # Create timer function
                t = threading.Timer(10, func)
                t.start()

            if len(self.added_group) >= 3:
                print "Running"
                t.cancel()
                func()
                # # print "group: {}".format(self.added_group)
                # self.valX = 0
                # self.valY = 0
                # self.valZ = 0
                # for self.added in self.added_group:
                #     # Convert new files using k2cosmos
                #     print "converting: {}".format(self.added)
                #     self.k2cosmos(self.added)
                #     time.sleep(3)

                #     # print 'Floor: {}'.format(self.added[0].split('.')[1].split('_')[1][1:])
                #     # Get floor threshold
                #     self.threshold = self.getFloorThreshold(self.added)

                #     # Run prism for new files
                #     # self.m0,self.m1,self.m2 = self.runPrism(self.threshold,self.inp,self.opt)
                #     # print "m0,m1,m2: {},{},{}".format(self.m0,self.m1,self.m2)
                #     self.vals = self.runPrism(self.opt)
                #     if self.vals[0][0] >= self.valX:
                #         self.valX = self.vals[0][0]
                #     elif self.vals[0][0] >= self.valX:
                #         self.valX = self.vals[0][0]
                #     elif self.vals[0][0] >= self.valX:
                #         self.valX = self.vals[0][0]

                #     # archive output
                #     self.archiveOut = os.path.join(histPath,'computed_parms\out')
                #     copy_tree(self.outPath,self.archiveOut)

                # self.vals = [(self.valX, 'X'), (self.valY, 'Y'), (self.valZ, 'Z')]
                # self.m0,self.m1,self.m2 = self.checkThreshold(self.inp, self.vals, self.threshold)
                # self.data_downloaded.emit((self.m0,self.m1,self.m2))
                # time.sleep(0.1)
                # self.added_group = []
            if self.removed:
                print "Removed: ", ", ".join(self.removed)
            self.before = self.after

    def k2cosmos(self,file):
        self.archiveIn = os.path.join(histPath,'computed_parms\in')
        # Convert the new file to cosmos file format
        self.file = file
        self.k2c = os.path.join(rootPath,'K2C')
        os.chdir(self.k2c)
        os.system('start /b K2COSMOS.exe "{}" -n1'.format(os.path.join(rawDataPath,self.file)))

        # Clear input/output prism path
        self.clearInOutDir()

        # Sleep for 5 seconds for conversion
        time.sleep(5)
        self.inPath = os.path.join(fpath,'computed_parms\in')
        for item in os.listdir(self.k2c):
            if item.endswith('.v0'):
                itemPath = os.path.join(self.k2c,item)
                sn = int(linecache.getline(itemPath,7).split()[3])
                shutil.move(os.path.join(self.k2c,item),os.path.join(self.inPath,item))
        copy_tree(self.inPath,self.archiveIn)
        print "Done converting to cosmos format..."
        return sn


    def clearInOutDir(self):
        self.inPath = os.path.join(fpath,'computed_parms\in')
        self.outPath = os.path.join(fpath,'computed_parms\out')
        
        try:
            shutil.rmtree(self.inPath)
            shutil.rmtree(self.outPath)
        except Exception as e:
            print e
            pass
        time.sleep(1)
        try:
            os.mkdir(self.inPath)
            os.mkdir(self.outPath)
        except:
            pass

    def computePrism(self):
        print "Computing seismograph parameters..."
        # Change directory to PRISM path and execute java file
        os.chdir(fpath)
        os.system("java -jar prism.jar ./computed_parms/in ./computed_parms/out ./config_files/prism_config.xml")
        print "Done."

    def readResults(self):
        print "Read results..."
        # Read result
        self.outPath = fpath + out
        for i,j,k in os.walk(self.outPath):
            if '\V2' in i:
                self.v2folder = i
                # print self.v2folder

        # Axis mapping
        self.axes = {'C1':'X','C2':'Y','C3':'Z'}

        # Get v2 distance files
        self.vals = []
        for fname in os.listdir(self.v2folder):
            if ".dis.V2" in fname:
                self.v2file = os.path.join(self.v2folder,fname)
                with open(self.v2file,'r') as f:
                    for i,line in enumerate(f):
                        if i == 10:
                            self.l = line.split(',')[2]
                            self.val = abs(float(self.l.split('at')[0].split()[2]))
                            self.unit = self.l.split('at')[0].split()[3]
                            self.axis = self.axes[fname.split('.')[-3]]
                            self.vals.append((self.val,self.axis))
        print self.vals
        return self.vals

    def replaceAlarm(self,opt):
        # Replace sound file depending on the choice
        with open(os.path.join(resourcePath,"sound.vbs"),'r') as f:
            for i,line in enumerate(f):
                if i == 1:
                    splitline = line.split('=')
                    splitline[1] = '"{}"'.format(opt)+'\n'
                    newline = ' = '.join(splitline)
        with open(os.path.join(resourcePath,"sound.vbs"),'r') as ff:
            allLines = ff.readlines()
            allLines[1] = newline
            # print allLines
        with open(os.path.join(resourcePath,"sounds.vbs"),'wb') as file:
            file.writelines(allLines)

    def runPrism(self, opt):
        # self.threshold = threshold
        # self.inp = inp
        self.opt = opt
        self.computePrism()
        time.sleep(2)
    
        while True:
            try:
                self.vals = self.readResults()
                break
            except Exception as e:
                print e
                self.vals = [(0.0, 'X'), (0.0, 'Y'), (0.0, 'Z')]
                break
            else:
                break
        self.replaceAlarm(self.opt)
        return self.vals

    def checkThreshold(self,inp,values,threshold):
        self.inp = inp
        self.values = values
        self.threshold = threshold
        # print self.values
        # print self.threshold

        # Get individual thresholds
        self.threshX = self.threshold[0]
        self.threshY = self.threshold[1]
        self.threshZ = self.threshold[2]

        # Message
        self.messages = []

        # Check if any of the value is greater than the threshold
        self.hit = None
        for i in range(len(self.values)):
            self.m = "Calculated {} cm at {}-axis or {}% allowable drift.<br>".format(self.values[i][0],self.values[i][1],(self.values[i][0]/self.threshold[i])*100)
            self.messages.append(self.m)
            if self.values[i][0] >= self.threshold[i]:
                self.hit = True
        print self.messages
        if self.hit is True:
            # if self.inp.lower() == 'a':
            #     os.system("start {}".format(os.path.join(resourcePath,'sound.vbs')))
            # else:
            #     os.system("start {}".format(os.path.join(resourcePath,'sound.vbs')))
            #     os.system("start {}".format(os.path.join(resourcePath,'alarm.vbs')))
            os.chdir(resourcePath)
            if self.inp.lower() == 'a':
                os.system("start sound.vbs")
            else:
                os.system("start sound.vbs")
                os.system("start alarm.vbs")

            self.message0 = "Event recorded.<br>"
            self.message1 = ' '.join(self.messages)
            self.message2 = "Threshold met. Evacuation recommended."
            # QtGui.QMessageBox.critical(self,"a","a",QtGui.QMessageBox.Ok)
            # QtGui.QMessageBox.about(self,"WARNING!!!","<font size = 40 color = red > {}{}</font><b><font size = 40 color = red > {} </font></b>".format(self.message0,self.message1,self.message2))
            # self.showAlarm(self.message0,self.message1,self.message2)
        else:
            self.message0 = "Event recorded.<br>"
            self.message1 = ' '.join(self.messages)
            self.message2 = "Threshold not met. Evacuation not necessary."
            # self.showNonAlarm(self.message0,self.message1,self.message2)
        return self.message0,self.message1,self.message2         


class Ui_MainWindow(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(Ui_MainWindow, self).__init__(parent)
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(485, 214)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 2, 1, 1, 1)
        self.commandLinkButton = QtGui.QCommandLinkButton(self.centralwidget)
        self.commandLinkButton.setObjectName(_fromUtf8("commandLinkButton"))
        self.gridLayout.addWidget(self.commandLinkButton, 5, 3, 1, 1)
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lineEdit = QtGui.QLineEdit(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit.sizePolicy().hasHeightForWidth())
        self.lineEdit.setSizePolicy(sizePolicy)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.horizontalLayout.addWidget(self.lineEdit)
        self.toolButton = QtGui.QToolButton(self.centralwidget)
        self.toolButton.setObjectName(_fromUtf8("toolButton"))
        self.horizontalLayout.addWidget(self.toolButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout_4, 2, 3, 2, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_2.addWidget(self.label_2)
        spacerItem1 = QtGui.QSpacerItem(80, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.label = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        font = QtGui.QFont()
        font.setPointSize(10)
        # font.setBold(True)
        font.setFamily(_fromUtf8("Roboto"))
        self.label.setFont(font)
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 4)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.radioButton_3 = QtGui.QRadioButton(self.centralwidget)
        self.radioButton_3.setObjectName(_fromUtf8("radioButton_3"))
        self.verticalLayout.addWidget(self.radioButton_3)
        self.radioButton = QtGui.QRadioButton(self.centralwidget)
        self.radioButton.setObjectName(_fromUtf8("radioButton"))
        self.verticalLayout.addWidget(self.radioButton)
        self.radioButton_2 = QtGui.QRadioButton(self.centralwidget)
        self.radioButton_2.setObjectName(_fromUtf8("radioButton_2"))
        self.verticalLayout.addWidget(self.radioButton_2)
        self.radioButton_4 = QtGui.QRadioButton(self.centralwidget)
        self.radioButton_4.setObjectName(_fromUtf8("radioButton_4"))
        self.verticalLayout.addWidget(self.radioButton_4)
        self.gridLayout.addLayout(self.verticalLayout, 2, 0, 3, 1)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 4, 3, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.pushButton_2 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.horizontalLayout_3.addWidget(self.pushButton_2)
        self.pushButton = QtGui.QPushButton(self.centralwidget)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.horizontalLayout_3.addWidget(self.pushButton)
        self.gridLayout.addLayout(self.horizontalLayout_3, 5, 0, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem3, 2, 2, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 485, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuAbout = QtGui.QMenu(self.menubar)
        self.menuAbout.setObjectName(_fromUtf8("menuAbout"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionHow_To_Use = QtGui.QAction(MainWindow)
        self.actionHow_To_Use.setObjectName(_fromUtf8("actionHow_To_Use"))
        self.actionVersion = QtGui.QAction(MainWindow)
        self.actionVersion.setObjectName(_fromUtf8("actionVersion"))
        self.actionLicense = QtGui.QAction(MainWindow)
        self.actionLicense.setObjectName(_fromUtf8("actionLicense"))
        self.menuAbout.addAction(self.actionHow_To_Use)
        self.menuAbout.addAction(self.actionVersion)
        self.menuAbout.addAction(self.actionLicense)
        self.menubar.addAction(self.menuAbout.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "GEOS SMA", None))
        self.commandLinkButton.setText(_translate("MainWindow", "View", None))
        self.toolButton.setToolTip(_translate("MainWindow", "<html><head/><body><p>Browse for the directory of a single output you want to visualize.</p></body></html>", None))
        self.toolButton.setText(_translate("MainWindow", "...", None))
        self.label_2.setText(_translate("MainWindow", "Select audio alert to use:", None))
        self.label.setText(_translate("MainWindow", "   View graph of an event:", None))
        self.radioButton_3.setToolTip(_translate("MainWindow", "<html><head/><body><p>Default siren alarm.</p></body></html>", None))
        self.radioButton_3.setText(_translate("MainWindow", "Default", None))
        self.radioButton.setToolTip(_translate("MainWindow", "<html><head/><body><p>Filipino advisory of Dr. Lagmay with siren alarm.</p></body></html>", None))
        self.radioButton.setText(_translate("MainWindow", "Filipino Advisory", None))
        self.radioButton_2.setToolTip(_translate("MainWindow", "<html><head/><body><p>English advisory by Dr. Lagmay with siren alarm.</p></body></html>", None))
        self.radioButton_2.setText(_translate("MainWindow", "Dr. Lagmay Advisory", None))
        self.radioButton_4.setToolTip(_translate("MainWindow", "<html><head/><body><p>Company specific advisory with siren alarm.</p></body></html>", None))
        self.radioButton_4.setText(_translate("MainWindow", "GEOS Advisory", None))
        self.pushButton_2.setText(_translate("MainWindow", "Run", None))
        self.pushButton.setText(_translate("MainWindow", "Quit", None))
        self.menuAbout.setTitle(_translate("MainWindow", "About", None))
        self.actionHow_To_Use.setText(_translate("MainWindow", "How To Use", None))
        self.actionVersion.setText(_translate("MainWindow", "Version", None))
        self.actionLicense.setText(_translate("MainWindow", "License", None))

        # Button listeners
        # self.connect(self.commandLinkButton, QtCore.SIGNAL("clicked()"),self.showPlot())
        # Show plot listener
        self.commandLinkButton.clicked.connect(self.showPlot)

        # Run/ Quit listener
        self.pushButton_2.clicked.connect(self.main)
        self.pushButton.clicked.connect(self.close)

        # Radio buttons
        QtCore.QObject.connect(self.radioButton_3,QtCore.SIGNAL("toggled(bool)"),self.radioDefault)
        QtCore.QObject.connect(self.radioButton,QtCore.SIGNAL("toggled(bool)"),self.radioFil)
        QtCore.QObject.connect(self.radioButton_2,QtCore.SIGNAL("toggled(bool)"),self.radioMahar)
        QtCore.QObject.connect(self.radioButton_4,QtCore.SIGNAL("toggled(bool)"),self.radioGEOS)

        # Browse folder button
        self.toolButton.clicked.connect(self.showDialog_root)

    # Button functions
    def showDialog_root(self):
        pathRoot = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory",'.'))
        self.lineEdit.setText(str(pathRoot))

    def showPlot(self):
        """
            Plot an event.
        """
        self.w = MyPopup()
        self.path = self.lineEdit.text()
        self.channels = {'X':{},'Y':{}}

        self.v2path = os.path.join(str(self.path),'V2')

        for item in os.listdir(self.v2path):
            itemPath = os.path.join(self.v2path,item)
            if 'C1' in itemPath:
                if 'acc' in itemPath:
                    with open(itemPath,'rb') as accFile:
                        # get line numbers
                        for index, line in enumerate(accFile):
                            if 'acceleration pts' in line:
                                ntime = line.split(',')[1].strip().split(' ')[3]
                                numLines =  int(line.strip().split(' ')[0])
                                startLine = index+1
                    with open(itemPath,'rb') as accFile:
                        accData = accFile.readlines()[startLine:startLine+numLines]
                        self.channels['X']['acc'] = accData

                if 'vel' in itemPath:
                    with open(itemPath,'rb') as velFile:
                        # get line numbers
                        for index, line in enumerate(velFile):
                            if 'velocity     pts' in line:
                                numLines =  int(line.strip().split(' ')[0])
                                startLine = index+1
                    with open(itemPath,'rb') as velFile:
                        velData = velFile.readlines()[startLine:startLine+numLines]
                        self.channels['X']['vel'] = velData

                if 'dis' in itemPath:
                    with open(itemPath,'rb') as disFile:
                        # get line numbers
                        for index, line in enumerate(disFile):
                            if 'displacement pts' in line:
                                numLines =  int(line.strip().split(' ')[0])
                                startLine = index+1
                    with open(itemPath,'rb') as disFile:
                        disData = disFile.readlines()[startLine:startLine+numLines]
                        self.channels['X']['dis'] = disData

            elif 'C2' in itemPath:
                if 'acc' in itemPath:
                    with open(itemPath,'rb') as accFile:
                        # get line numbers
                        for index, line in enumerate(accFile):
                            if 'acceleration pts' in line:
                                numLines =  int(line.strip().split(' ')[0])
                                startLine = index+1
                    with open(itemPath,'rb') as accFile:
                        accData = accFile.readlines()[startLine:startLine+numLines]
                        self.channels['Y']['acc'] = accData

                if 'vel' in itemPath:
                    with open(itemPath,'rb') as velFile:
                        # get line numbers
                        for index, line in enumerate(velFile):
                            if 'velocity     pts' in line:
                                numLines =  int(line.strip().split(' ')[0])
                                startLine = index+1
                    with open(itemPath,'rb') as velFile:
                        velData = velFile.readlines()[startLine:startLine+numLines]
                        self.channels['Y']['vel'] = velData

                if 'dis' in itemPath:
                    with open(itemPath,'rb') as disFile:
                        # get line numbers
                        for index, line in enumerate(disFile):
                            if 'displacement pts' in line:
                                numLines =  int(line.strip().split(' ')[0])
                                startLine = index+1
                    with open(itemPath,'rb') as disFile:
                        disData = disFile.readlines()[startLine:startLine+numLines]
                        self.channels['Y']['dis'] = disData

                # if 'vel' in itemPath:
                #     with open(itemPath,'rb') as velFile:
                #         f = velFile.readlines()
                #         numLines =  int(f[51].strip().split(' ')[0])
                #         velData = f[52:52+numLines]

                # if 'dis' in itemPath:
                #     with open(itemPath,'rb') as disFile:
                #         f = disFile.readlines()
                #         numLines =  int(f[51].strip().split(' ')[0])
                #         disData = f[52:52+numLines]

        x_time = np.linspace(0,float(ntime),num=numLines)
        ax0 = self.w.figure.add_subplot(321)
        ax0.plot(x_time,self.channels['X']['acc'],'b-', label='acceleration')
        ax0.legend(loc=4)
        ax0.set_xlabel('time (s)')
        ax0.set_ylabel('acceleration (cm/sec2)')
        ax0.set_title('X axis data')

        ax1 = self.w.figure.add_subplot(323)
        ax1.plot(x_time,self.channels['X']['vel'],'g-', label='velocity')
        ax1.legend(loc=4)
        ax1.set_xlabel('time (s)')
        ax1.set_ylabel('velocity (cm/sec)')

        ax2 = self.w.figure.add_subplot(325)
        ax2.plot(x_time,self.channels['X']['dis'],'r-', label='displacement')
        ax2.legend(loc=4)
        ax2.set_xlabel('time (s)')
        ax2.set_ylabel('displacement (cm)')


        ax3 = self.w.figure.add_subplot(322)
        ax3.plot(x_time,self.channels['Y']['acc'],'b-', label='acceleration')
        ax3.legend(loc=4)
        ax3.set_xlabel('time (s)')
        ax3.set_ylabel('acceleration (cm/sec2)')
        ax3.set_title('Y axis data')

        ax4 = self.w.figure.add_subplot(324)
        ax4.plot(x_time,self.channels['Y']['vel'],'g-', label='velocity')
        ax4.legend(loc=4)
        ax4.set_xlabel('time (s)')
        ax4.set_ylabel('velocity (cm/sec)')

        ax5 = self.w.figure.add_subplot(326)
        ax5.plot(x_time,self.channels['Y']['dis'],'r-', label='displacement')
        ax5.legend(loc=4)
        ax5.set_xlabel('time (s)')
        ax5.set_ylabel('displacement (cm)')

        # ax = self.w.figure.add_subplot(111)
        # ax.plot(self.channels['X'][2],self.channels['Y'][2],'r-', label='displacement')

        self.w.canvas.draw()
        self.w.show()




    # Radios
    def radioDefault(self):
        Ui_MainWindow.radio = 'a'

    def radioFil(self):
        Ui_MainWindow.radio = 'b'

    def radioMahar(self):
        Ui_MainWindow.radio = 'c'

    def radioGEOS(self):
        Ui_MainWindow.radio = 'd'

    def readRadioButton(self):
        self.opt = None
        if Ui_MainWindow.radio == None:
            print "Please choose audio alert to use"
        elif Ui_MainWindow.radio == 'a':
            self.opt = "MandatoryEvacuationSounds.mp3"
        elif Ui_MainWindow.radio == 'b':
            self.opt = "audio1.mp3"
        elif Ui_MainWindow.radio == 'c':
            self.opt = "audio2.mp3"
        elif Ui_MainWindow.radio == 'd':
            self.opt = "audio3.mp3"

        return Ui_MainWindow.radio,self.opt

    def close(self):
        def kill_proc_tree(pid, including_parent=True):    
            parent = psutil.Process(pid)
            if including_parent:
                parent.kill()
        me = os.getpid()
        kill_proc_tree(me)
        QtGui.qApp.closeAllWindows()

    def main(self):
        # self.syncFiles()
        self.inp,self.opt = self.readRadioButton()
        self.monitorer = MonitorThread(self.inp,self.opt)
        self.monitorer.data_downloaded.connect(self.on_data_ready)
        self.monitorer.start()

    def on_data_ready(self, data):
        print "dat: ".format(data)
        print data[0]
        print data[1]
        print data[2]
        if 'Threshold met' in data[2]:
            QtGui.QMessageBox.warning(self,"Alert!","<font size = 40 color = red > {}{}</font><b><font size = 40 color = red > {} </font></b>".format(data[0],data[1],data[2]))
        else:
            QtGui.QMessageBox.about(self,"Event","<font size=20 color=green>{}{}</font><b><font size = 20 color = green > {} </font></b>".format(data[0],data[1],data[2]))



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())