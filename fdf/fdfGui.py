# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fdfGui-V01-5.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from frozentable import FreezeTableWidget  # Changed

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

class Ui_MainWindow(object):
    def setupUi(self, model, MainWindow):  # Changed
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1180, 873)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 9)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.groupBoxFileDetails = QtGui.QGroupBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(200)
        sizePolicy.setHeightForWidth(self.groupBoxFileDetails.sizePolicy().hasHeightForWidth())
        self.groupBoxFileDetails.setSizePolicy(sizePolicy)
        self.groupBoxFileDetails.setObjectName(_fromUtf8("groupBoxFileDetails"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.groupBoxFileDetails)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.labelInstrument = QtGui.QLabel(self.groupBoxFileDetails)
        self.labelInstrument.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelInstrument.sizePolicy().hasHeightForWidth())
        self.labelInstrument.setSizePolicy(sizePolicy)
        self.labelInstrument.setMinimumSize(QtCore.QSize(100, 0))
        self.labelInstrument.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.labelInstrument.setObjectName(_fromUtf8("labelInstrument"))
        self.horizontalLayout_5.addWidget(self.labelInstrument)
        self.instrumentComboBox = QtGui.QComboBox(self.groupBoxFileDetails)
        self.instrumentComboBox.setMinimumSize(QtCore.QSize(133, 0))
        self.instrumentComboBox.setObjectName(_fromUtf8("instrumentComboBox"))
        self.horizontalLayout_5.addWidget(self.instrumentComboBox)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.labelFileLocation = QtGui.QLabel(self.groupBoxFileDetails)
        self.labelFileLocation.setObjectName(_fromUtf8("labelFileLocation"))
        self.horizontalLayout_4.addWidget(self.labelFileLocation)
        self.filePickerBtn = QtGui.QToolButton(self.groupBoxFileDetails)
        self.filePickerBtn.setObjectName(_fromUtf8("filePickerBtn"))
        self.horizontalLayout_4.addWidget(self.filePickerBtn)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.fileLineEdit = QtGui.QLineEdit(self.groupBoxFileDetails)
        self.fileLineEdit.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fileLineEdit.sizePolicy().hasHeightForWidth())
        self.fileLineEdit.setSizePolicy(sizePolicy)
        self.fileLineEdit.setMinimumSize(QtCore.QSize(200, 0))
        self.fileLineEdit.setObjectName(_fromUtf8("fileLineEdit"))
        self.horizontalLayout_4.addWidget(self.fileLineEdit)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.labelDateFormat = QtGui.QLabel(self.groupBoxFileDetails)
        self.labelDateFormat.setEnabled(True)
        self.labelDateFormat.setObjectName(_fromUtf8("labelDateFormat"))
        self.horizontalLayout_2.addWidget(self.labelDateFormat)
        self.dateFormatComboBox = QtGui.QComboBox(self.groupBoxFileDetails)
        self.dateFormatComboBox.setObjectName(_fromUtf8("dateFormatComboBox"))
        self.horizontalLayout_2.addWidget(self.dateFormatComboBox)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.addFileBtn = QtGui.QPushButton(self.groupBoxFileDetails)
        self.addFileBtn.setObjectName(_fromUtf8("addFileBtn"))
        self.verticalLayout_3.addWidget(self.addFileBtn)
        self.horizontalLayout.addWidget(self.groupBoxFileDetails)
        self.layoutCurrentFilesVertical = QtGui.QVBoxLayout()
        self.layoutCurrentFilesVertical.setObjectName(_fromUtf8("layoutCurrentFilesVertical"))
        self.labelCurrentFiles = QtGui.QLabel(self.centralwidget)
        self.labelCurrentFiles.setObjectName(_fromUtf8("labelCurrentFiles"))
        self.layoutCurrentFilesVertical.addWidget(self.labelCurrentFiles)
        self.listWidgetCurrentFiles = QtGui.QListWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidgetCurrentFiles.sizePolicy().hasHeightForWidth())
        self.listWidgetCurrentFiles.setSizePolicy(sizePolicy)
        self.listWidgetCurrentFiles.setMinimumSize(QtCore.QSize(400, 0))
        self.listWidgetCurrentFiles.setMaximumSize(QtCore.QSize(16777215, 100))
        self.listWidgetCurrentFiles.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.listWidgetCurrentFiles.setObjectName(_fromUtf8("listWidgetCurrentFiles"))
        self.layoutCurrentFilesVertical.addWidget(self.listWidgetCurrentFiles)
        self.horizontalLayout.addLayout(self.layoutCurrentFilesVertical)
        self.groupBoxEditTools = QtGui.QGroupBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(200)
        sizePolicy.setHeightForWidth(self.groupBoxEditTools.sizePolicy().hasHeightForWidth())
        self.groupBoxEditTools.setSizePolicy(sizePolicy)
        self.groupBoxEditTools.setObjectName(_fromUtf8("groupBoxEditTools"))
        self.gridLayout_3 = QtGui.QGridLayout(self.groupBoxEditTools)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.pushButtonDeleteLines = QtGui.QPushButton(self.groupBoxEditTools)
        self.pushButtonDeleteLines.setObjectName(_fromUtf8("pushButtonDeleteLines"))
        self.gridLayout_3.addWidget(self.pushButtonDeleteLines, 2, 0, 1, 1)
        self.pushButtonAddLines = QtGui.QPushButton(self.groupBoxEditTools)
        self.pushButtonAddLines.setObjectName(_fromUtf8("pushButtonAddLines"))
        self.gridLayout_3.addWidget(self.pushButtonAddLines, 1, 0, 1, 1)
        self.pushButtonExportData = QtGui.QPushButton(self.groupBoxEditTools)
        self.pushButtonExportData.setObjectName(_fromUtf8("pushButtonExportData"))
        self.gridLayout_3.addWidget(self.pushButtonExportData, 1, 1, 1, 1)
        self.pushButtonResetData = QtGui.QPushButton(self.groupBoxEditTools)
        self.pushButtonResetData.setObjectName(_fromUtf8("pushButtonResetData"))
        self.gridLayout_3.addWidget(self.pushButtonResetData, 2, 1, 1, 1)
        self.chkBoxSampleOriented = QtGui.QCheckBox(self.groupBoxEditTools)
        self.chkBoxSampleOriented.setObjectName(_fromUtf8("chkBoxSampleOriented"))
        self.gridLayout_3.addWidget(self.chkBoxSampleOriented, 1, 2, 1, 1)
        self.pushButtonSwapDayMonth = QtGui.QPushButton(self.groupBoxEditTools)
        self.pushButtonSwapDayMonth.setObjectName(_fromUtf8("pushButtonSwapDayMonth"))
        self.gridLayout_3.addWidget(self.pushButtonSwapDayMonth, 3, 0, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.labelFrozenColumns = QtGui.QLabel(self.groupBoxEditTools)
        self.labelFrozenColumns.setObjectName(_fromUtf8("labelFrozenColumns"))
        self.horizontalLayout_3.addWidget(self.labelFrozenColumns)
        self.spinBoxFrozenColumns = QtGui.QSpinBox(self.groupBoxEditTools)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBoxFrozenColumns.sizePolicy().hasHeightForWidth())
        self.spinBoxFrozenColumns.setSizePolicy(sizePolicy)
        self.spinBoxFrozenColumns.setAlignment(QtCore.Qt.AlignCenter)
        self.spinBoxFrozenColumns.setMaximum(13)
        self.spinBoxFrozenColumns.setProperty("value", 3)
        self.spinBoxFrozenColumns.setObjectName(_fromUtf8("spinBoxFrozenColumns"))
        self.horizontalLayout_3.addWidget(self.spinBoxFrozenColumns)
        self.gridLayout_3.addLayout(self.horizontalLayout_3, 3, 1, 1, 1)
        self.horizontalLayout.addWidget(self.groupBoxEditTools)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        spacerItem3 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout_2.addItem(spacerItem3)
        self.tableViewData = FreezeTableWidget(model, self.centralwidget)  # Changed
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableViewData.sizePolicy().hasHeightForWidth())
        self.tableViewData.setSizePolicy(sizePolicy)
        self.tableViewData.setMinimumSize(QtCore.QSize(0, 500))
        self.tableViewData.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.tableViewData.setObjectName(_fromUtf8("tableViewData"))
        self.verticalLayout_2.addWidget(self.tableViewData)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1180, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionHelp = QtGui.QAction(MainWindow)
        self.actionHelp.setObjectName(_fromUtf8("actionHelp"))
        self.actionAbout = QtGui.QAction(MainWindow)
        self.actionAbout.setObjectName(_fromUtf8("actionAbout"))
        self.menuHelp.addAction(self.actionHelp)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "FDF - Field Data Formatter", None))
        self.groupBoxFileDetails.setTitle(_translate("MainWindow", "File details", None))
        self.labelInstrument.setText(_translate("MainWindow", "Instrument", None))
        self.labelFileLocation.setText(_translate("MainWindow", "File location", None))
        self.filePickerBtn.setText(_translate("MainWindow", "...", None))
        self.labelDateFormat.setText(_translate("MainWindow", "Date format of file", None))
        self.addFileBtn.setText(_translate("MainWindow", "Add file", None))
        self.labelCurrentFiles.setText(_translate("MainWindow", "Current files", None))
        self.groupBoxEditTools.setTitle(_translate("MainWindow", "Edit tools", None))
        self.pushButtonDeleteLines.setText(_translate("MainWindow", "Delete selected", None))
        self.pushButtonAddLines.setText(_translate("MainWindow", "Add lines", None))
        self.pushButtonExportData.setText(_translate("MainWindow", "Export data", None))
        self.pushButtonResetData.setText(_translate("MainWindow", "Reset data", None))
        self.chkBoxSampleOriented.setText(_translate("MainWindow", "Export sample-oriented file", None))
        self.pushButtonSwapDayMonth.setText(_translate("MainWindow", "Swap day and month", None))
        self.labelFrozenColumns.setText(_translate("MainWindow", "Frozen columns", None))
        self.menuHelp.setTitle(_translate("MainWindow", "Help", None))
        self.actionHelp.setText(_translate("MainWindow", "Help", None))
        self.actionAbout.setText(_translate("MainWindow", "About", None))

