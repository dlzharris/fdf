"""
Module: fdf.py
Runs the KiWQM Field Data Formatter GUI, used to generate a valid
field data import file for KiWQM.

Author: Daniel Harris
Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/12/2016

External dependencies: PyYAML, PyQT4

Classes:
MainApp: Constructor for the main application.
TableModel: Model part of PyQT MVC framework for storing the tabular data

Functions:
Main: Runs the Field Data Formatter app.
"""

# Standard library imports
import datetime
import operator
import os
import sys
import urllib2

# Related third party imports
import yaml
from PyQt4 import QtGui, QtCore

# Local application imports
import fdfGui
import functions
import settings
from functions import ValidityError, DatetimeError
from settings import app_config, column_config
from delegates import TableDelegate

__author__ = 'Daniel Harris'
__date__ = '03 March 2017'
__email__ = 'daniel.harris@dpi.nsw.gov.au'
__status__ = 'Production'
__version__ = '1.0.0'


###############################################################################
# Models
###############################################################################
class TableModel(QtCore.QAbstractTableModel):
    # Define a signal for use in the view
    verticalHeaderChanged = QtCore.pyqtSignal()

    def __init__(self, undoStack, samples=[], headers=[], parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._samples = samples
        self._headers = headers
        self.undoStack = undoStack

        if not self._samples:
            self._samples.append(self.defaultData())

    ##########################################################################
    # Reimplemented methods
    ##########################################################################
    def columnCount(self, parent=None):
        return len(column_config)

    def rowCount(self, parent=None):
        return len(self._samples)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        column = index.column()
        value = self._samples[row][column]

        if role == QtCore.Qt.DisplayRole:
            # Dates and times
            if type(value) in (QtCore.QDate, QtCore.QTime):
                value = value.toString(QtCore.Qt.ISODate)
            # Floating point numbers
            if value and 'lower_limit' in column_config[column]:
                value = QtCore.QString.number(value, 'f', column_config[column]['precision'])
            return value

        if role == QtCore.Qt.EditRole:
            return value

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter

        if role == QtCore.Qt.BackgroundRole:
            return self.validateData(value, index)[0]

        if role == QtCore.Qt.ToolTipRole:
            return self.validateData(value, index)[1]

    def flags(self, index):
        if index.column() == functions.get_column_number('sampling_number'):
            flags = QtCore.Qt.ItemIsEnabled
        else:
            flags = QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return flags

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return column_config[section]['display_name']
            else:
                self.verticalHeaderChanged.emit()
                return section + 1

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self._samples.insert(position, self.defaultData())
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            del self._samples[position + i]
        self.endRemoveRows()
        return True

    def setData(self, index, value, role=QtCore.Qt.EditRole, *args, **kwargs):
        if index.isValid() and role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()

            dateFormat = kwargs.get('dateFormat')

            # Date as QDate object
            if column == functions.get_column_number('date'):
                if type(value) is QtCore.QDate:
                    pass
                else:
                    # Change value to a string so it can be parsed
                    date = str(value)
                    try:
                        dt_dayfirst = True if dateFormat[:2] == 'dd' else False
                    except TypeError:
                        dt_dayfirst = False
                    try:
                        dt_yearfirst = True if dateFormat[:2] == 'YY' else False
                    except TypeError:
                        dt_yearfirst = False
                    try:
                        dt = functions.parse_datetime_from_string(date, "", dayfirst=dt_dayfirst, yearfirst=dt_yearfirst)
                        value = QtCore.QDate(dt.year, dt.month, dt.day)
                    except DatetimeError:
                        value = ""

            # Time as QTime object
            if column == functions.get_column_number('time'):
                if type(value) is QtCore.QTime:
                    pass
                else:
                    # Change value to a string so it can be parsed
                    time = str(value)
                    dt = functions.parse_datetime_from_string("", time)
                    value = QtCore.QTime(dt.hour, dt.minute, dt.second)

            # Update sampling number
            if column in (functions.get_column_number('station_number'),
                          functions.get_column_number('date'),
                          functions.get_column_number('sample_type')):
                sampling_number = self.getSamplingNumber(value, index)
                self._samples[row][functions.get_column_number('sampling_number')] = sampling_number
                # Tell the view that the sampling number has changed
                idxChanged = self.index(row, functions.get_column_number('sampling_number'))
                self.dataChanged.emit(idxChanged, idxChanged)

            # Floating point numbers
            if value and 'lower_limit' in column_config[column]:
                value = float(value)

            # Update coordinate values
            if column in [functions.get_column_number('latitude'), functions.get_column_number('longitude')]:
                try:
                    if column == functions.get_column_number('latitude'):
                        # Ensure latitude is always south (negative)
                        if value > 0:
                            value *= -1
                        latitude = value
                        longitude = self.data(self.index(row, functions.get_column_number('longitude')),
                                              QtCore.Qt.EditRole)
                    else:
                        latitude = self.data(self.index(row, functions.get_column_number('latitude')),
                                             QtCore.Qt.EditRole)
                        longitude = value

                    # Calculate MGA94 coordinates
                    easting, northing, map_zone = functions.get_mga_coordinates(latitude, longitude)

                    # Set MGA94 coordinates
                    self._samples[row][functions.get_column_number('easting')] = easting
                    idxChanged = self.index(row, functions.get_column_number('easting'))
                    self.dataChanged.emit(idxChanged, idxChanged)

                    self._samples[row][functions.get_column_number('northing')] = northing
                    idxChanged = self.index(row, functions.get_column_number('northing'))
                    self.dataChanged.emit(idxChanged, idxChanged)

                    self._samples[row][functions.get_column_number('map_zone')] = map_zone
                    idxChanged = self.index(row, functions.get_column_number('map_zone'))
                    self.dataChanged.emit(idxChanged, idxChanged)
                except ValueError:
                    pass

            self._samples[row][column] = value
            self.dataChanged.emit(index, index)
            return True

        return False

    ##########################################################################
    # Private methods
    ##########################################################################
    def checkMatrixConsistency(self):
        """
        Checks that all samples in a single sampling use the same matrix.
        This is a requirement for KiWQM.
        :return: Boolean indicating if matrix is consistent or not
        """
        matrix_consistent = True
        matrix_list = []

        for row in range(self.rowCount()):
            matrix_list.append(
                (self._samples[row][functions.get_column_number('mp_number')],
                 self._samples[row][functions.get_column_number('sample_matrix')],
                 self._samples[row][functions.get_column_number('sampling_number')])
            )

        for sample in matrix_list:
            # Get a list of all matrices in a single sampling.
            sampling_matrix = [x for (m, x, s) in matrix_list if m == sample[0] and s == sample[2]]
            # Check that each sampling only has one matrix
            if len(set(sampling_matrix)) > 1:
                matrix_consistent = False
                break

        return matrix_consistent

    def checkSequenceNumbers(self):
        """
        Checks that all samples in a single sampling use distinct sequence
        numbers and that they start at 1 and increment sequentially.
        :return: Boolean indicating if sequence numbers are acceptable
        """
        sequence_correct = True
        sequence_list = []

        try:
            for row in range(self.rowCount()):
                sequence_list.append(
                    (self._samples[row][functions.get_column_number('mp_number')],
                     self._samples[row][functions.get_column_number('sample_cid')],
                     self._samples[row][functions.get_column_number('sampling_number')],
                     self._samples[row][functions.get_column_number('location_id')],
                     self._samples[row][functions.get_column_number('sample_collected')])
                )

            for sample in sequence_list:
                # Get a list of all sequence numbers at a single location in a
                # single sampling.
                sequence_numbers = [
                    int(s) for (m, s, n, l, c) in sequence_list if
                    m == sample[0] and
                    n == sample[2] and
                    l == sample[3] and
                    c != "NO"
                    ]
                # Check that sequence numbers in a single sampling are distinct,
                # start at 1, and increment sequentially
                if not all(a == b for a, b in list(enumerate(sorted(sequence_numbers), start=1))):
                    sequence_correct = False

        # If we are missing sampling numbers or location IDs then we will get a ValueError
        except ValueError:
            sequence_correct = False

        return sequence_correct

    def defaultData(self):
        """
        Generates a row of empty QStrings to initialise an empty data row
        :return: List of QStrings
        """
        defaultValues = [QtCore.QString("") for column in range(len(column_config))]
        defaultValues[functions.get_column_number('date')] = QtCore.QDate()
        defaultValues[functions.get_column_number('time')] = QtCore.QTime()
        return defaultValues

    def getSamplingNumber(self, value, index):
        """
        Returns a new sampling number
        :param value: The value to use for the update. This will be the
        station number, date or sample type.
        :index: Model index of the value
        :return: String of well-formatted sampling identification number
        """
        row = index.row()
        column = index.column()

        if column == functions.get_column_number('station_number'):
            station_number = value
            date = self._samples[row][functions.get_column_number('date')].toPyDate() \
                .strftime(app_config['datetime_formats']['date']['sampling_number'])
            sample_type = self._samples[row][functions.get_column_number('sample_type')]

        elif column == functions.get_column_number('date') and value:
            station_number = self._samples[row][functions.get_column_number('station_number')]
            date = value.toPyDate().strftime(app_config['datetime_formats']['date']['sampling_number'])
            sample_type = self._samples[row][functions.get_column_number('sample_type')]

        elif column == functions.get_column_number('sample_type'):
            station_number = self._samples[row][functions.get_column_number('station_number')]
            date = self._samples[row][functions.get_column_number('date')].toPyDate() \
                .strftime(app_config['datetime_formats']['date']['sampling_number'])
            sample_type = value

        else:
            station_number = self._samples[row][functions.get_column_number('station_number')]
            date = self._samples[row][functions.get_column_number('date')].toPyDate() \
                .strftime(app_config['datetime_formats']['date']['sampling_number'])
            sample_type = self._samples[row][functions.get_column_number('sample_type')]

        # Create the sampling number in format STATION#-DDMMYY[-SAMPLE_TYPE]
        # Check if any components are empty or if date is not valid
        if (not station_number) or (not date) or date == '010123':
            sampling_number = ""
        elif sample_type in ["QR", "QB", "QT"]:
            sampling_number = QtCore.QString("%1-%2-%3").arg(station_number).arg(date).arg(sample_type)
        else:
            sampling_number = QtCore.QString("%1-%2").arg(station_number).arg(date)
        return QtCore.QString(sampling_number)

    def resetData(self):
        """
        Reset all data in model
        :return: None
        """
        for i in range(self.rowCount(), 0, -1):
            self.removeRow(i - 1)

    def validateData(self, value, index):
        """
        Validates model data and returns a cell colour and tooltip for
        invalid cells.
        :param value: Value to be validated
        :param index: Model index of the value to be validated
        :return: QBrush colour and tooltip text
        """
        # Zero values must be test first because second test will return False
        if value == 0 and 'lower_limit' in column_config[index.column()]:
            text = "Given value is zero (0). A value of zero generally indicates a sensor failure, " \
                   "or a non-measured parameter. Please review and adjust before continuing."
            return QtGui.QBrush(QtCore.Qt.red), text

        elif value:
            if index.column() == functions.get_column_number('date') and value > QtCore.QDate.currentDate():
                text = "The entered date is in the future. Sampling dates must be in the past.\n" \
                          "Please enter a different date."
                return QtGui.QBrush(QtCore.Qt.red), text

            if index.column() == functions.get_column_number('date') and not value.isValid():
                text = "The entered date is invalid. Please enter a valid date."
                return QtGui.QBrush(QtCore.Qt.red), text

            if index.column() == functions.get_column_number('time') and not value.isValid():
                text = "The entered time is invalid. Please enter a valid time."
                return QtGui.QBrush(QtCore.Qt.red), text

            if 'lower_limit' in column_config[index.column()]:
                 if value < column_config[index.column()]['lower_limit'] or value > column_config[index.column()]['upper_limit']:
                    lowerLimit = column_config[index.column()]['lower_limit']
                    upperLimit = column_config[index.column()]['upper_limit']
                    text = "Value out of range.\nAcceptable range is between %s and %s" % (lowerLimit, upperLimit)
                    return QtGui.QBrush(QtCore.Qt.red), text

            if 'list_items' in column_config[index.column()] and value not in column_config[index.column()]['list_items']:
                text = "Value is not a valid value from the drop down list.\n" \
                      "Please select a valid value from the list."
                return QtGui.QBrush(QtCore.Qt.red), text

        return QtGui.QBrush(QtCore.Qt.white), None

    def sort(self, column, order):
        """Sort table by given column number"""
        # Clear the undo stack
        self.undoStack.clear()
        # Begin sorting
        self.layoutAboutToBeChanged.emit()
        self._samples = sorted(self._samples, key=operator.itemgetter(column))
        if order == QtCore.Qt.DescendingOrder:
            self._samples.reverse()
        self.layoutChanged.emit()

    def swapMonthDay(self, listOfIndexes):
        """
        Swaps the month and day values for dates where that results in a
        valid date.
        :param listOfIndexes: List of model indexes to be swapped.
        :return: None
        """
        for index in listOfIndexes:
            if index.column() == functions.get_column_number('date'):
                # Get current settings
                day = self.data(index, QtCore.Qt.EditRole).day()
                month = self.data(index, QtCore.Qt.EditRole).month()
                year = self.data(index, QtCore.Qt.EditRole).year()
                # Swap day and month
                if day <= 12:
                    date = QtCore.QDate(year, day, month)
                    self.setData(index, date)


###############################################################################
# Undo action commands
###############################################################################
class CommandSetData(QtGui.QUndoCommand):
    def __init__(self, model, index, value, previous, description="Item edited", *args, **kwargs):
        super(CommandSetData, self).__init__(description)
        self.model = model
        self.index = index
        self.value = value
        self.previous = previous
        self.dateFormat = kwargs.get('dateFormat')

    def redo(self):
        if self.dateFormat:
            self.model.setData(self.index, self.value, dateFormat=self.dateFormat)
        else:
            self.model.setData(self.index, self.value)

    def undo(self):
        self.model.setData(self.index, self.previous)


###############################################################################
# Main app constructor and initialisation
###############################################################################
class MainApp(fdfGui.Ui_MainWindow, QtGui.QMainWindow):
    """
    Constructor for the main application
    """
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        # Check we are using the latest version of FDF
        self.checkVersion()
        # Set up the undo stack
        self.undoStack = QtGui.QUndoStack(self)
        # Set up model
        self.sampleModel = TableModel(undoStack=self.undoStack)
        self.sampleModel.removeRows(0, 1)
        # Set up the main GUI window
        self.setupUi(self.sampleModel, self)
        # Initialise global variables
        settings.FROZEN_COLUMNS = self.spinBoxFrozenColumns.value()
        # Set up the table views
        self.tableViewData.setItemDelegate(TableDelegate(False))
        self.tableViewData.frozenTableView.setItemDelegate(TableDelegate(True))
        self.tableViewData.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tableViewData.setSortingEnabled(True)
        # Connect signals
        self.tableViewData.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.filePickerBtn.clicked.connect(self.filePicker)
        self.addFileBtn.clicked.connect(self.addFile)
        self.pushButtonDeleteLines.clicked.connect(self.delRows)
        self.pushButtonAddLines.clicked.connect(self.insertRows)
        self.pushButtonResetData.clicked.connect(self.resetData)
        self.pushButtonExportData.clicked.connect(self.exportData)
        self.pushButtonSwapDayMonth.clicked.connect(self.swapDayMonth)
        self.pushButtonFillSampleLocation.clicked.connect(self.fillSampleLocation)
        self.spinBoxFrozenColumns.valueChanged.connect(self.tableViewData.updateFrozenColumns)
        self.spinBoxFrozenColumns.valueChanged.connect(self.updateGlobalFrozenColumns)

        # Add items to the instrument picker
        instruments = ['']
        instruments.extend(app_config['sources']['hydrolab'])
        instruments.extend(app_config['sources']['ysi'])
        self.instrumentComboBox.addItems(instruments)

        # Set up the date format picker
        dateFormats = ['dd/MM/yyyy', 'MM/dd/yyyy', 'yyyy-MM-dd']
        self.dateFormatComboBox.addItems(dateFormats)

        # Set up the help documentation
        self.helpBrowser = QtGui.QTextBrowser()
        self.helpBrowser.setSource(QtCore.QUrl('help.html'))
        self.helpBrowser.setWindowTitle(u"FDF Utility Help Documentation")
        self.helpBrowser.setMinimumSize(500, 500)
        self.actionHelp.triggered.connect(self.showHelp)

        # Set up the about documentation
        self.actionAbout.triggered.connect(self.showAbout)

        # Ensure the window is deleted on close to prevent threading errors
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    ##########################################################################
    # Reimplemented methods
    ##########################################################################
    def contextMenuEvent(self, event):
        if event.Reason() == QtGui.QContextMenuEvent.Mouse:
            menu = QtGui.QMenu(self)
            menu.addAction(u"Undo", self.undo, QtGui.QKeySequence.Undo)
            menu.addAction(u"Redo", self.redo, QtGui.QKeySequence.Redo)
            menu.addSeparator()
            menu.addAction(u"Copy", self.copy, QtGui.QKeySequence.Copy)
            menu.addAction(u"Cut", self.copy, QtGui.QKeySequence.Cut)
            menu.addAction(u"Paste", self.paste, QtGui.QKeySequence.Paste)
            menu.popup(QtGui.QCursor.pos())

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.copy()
        elif event.matches(QtGui.QKeySequence.Cut):
            self.cut()
        elif event.matches(QtGui.QKeySequence.Delete):
            self.delete()
        elif event.matches(QtGui.QKeySequence.Paste):
            self.paste()
        elif event.matches(QtGui.QKeySequence.Undo):
            self.undo()
        elif event.matches(QtGui.QKeySequence.Redo):
            self.redo()
        elif event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.keyPressEnter()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.clearSelection()
        else:
            QtGui.QMainWindow.keyPressEvent(self, event)

    ##########################################################################
    # Private methods
    ##########################################################################
    def addFile(self):
        """Loads the file specified in the UI and adds it to the table instance."""
        try:
            # Validate file type
            dicts = functions.load_instrument_file(
                self.fileLineEdit.text(),
                str(self.instrumentComboBox.currentText()),
                str(self.dateFormatComboBox.currentText())
            )

            # Add data to table
            lists = functions.lord2lorl(dicts, app_config['column_order'])

            fileValid = True

            for i in range(len(lists)):
                self.sampleModel.insertRows(self.sampleModel.rowCount(), 1)
                for j in range(len(lists[i])):
                    index = self.sampleModel.index(self.sampleModel.rowCount() - 1, j)
                    self.sampleModel.setData(index, lists[i][j])
                    # If we have an invalid value, change the valid flag so that the message displays
                    if self.sampleModel.data(index, role=QtCore.Qt.BackgroundRole) == QtGui.QBrush(QtCore.Qt.red):
                        fileValid = False

            # Add file name to listbox
            self.listWidgetCurrentFiles.addItem(QtGui.QListWidgetItem(self.fileLineEdit.text()))

            if not fileValid:
                txt = u"The chosen file has invalid values.\n\n" \
                      u"Please review the cells in red highlight before exporting."
                msg = QtGui.QMessageBox()
                msg.setIcon(QtGui.QMessageBox.Warning)
                msg.setText(txt)
                msg.setWindowTitle(u"Errors detected!")
                msg.exec_()

        except ValidityError:
            txt = u"The chosen file is not valid for the specified instrument.\n\n" \
                  u"Please select a different file or a different instrument from the drop-down list."
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(txt)
            msg.setWindowTitle(u"File validity error!")
            msg.exec_()

    def checkVersion(self):
        """
        Checks the version of FDF utility to ensure it is up-to-date.
        Displays a message if the utility is out of date.
        """
        version_url = u'https://raw.githubusercontent.com/dlzharris/fdf/master/current_version.txt'
        package_url = u'https://github.com/dlzharris/fdf/releases'

        try:
            proxy = urllib2.ProxyHandler({'http': 'oranprodproxy.dpi.nsw.gov.au:8080',
                                          'https': 'oranprodproxy.dpi.nsw.gov.au:8080'})
            opener = urllib2.build_opener(proxy)
            urllib2.install_opener(opener)
            if __status__ == 'Development':
                current_version = yaml.load(urllib2.urlopen(version_url).read())['version_dev']
            else:
                current_version = yaml.load(urllib2.urlopen(version_url).read())['version_stable']
        except urllib2.URLError:
            return None

        if __version__ != current_version:
            txt = u"There is a newer version of this application available. " \
                  u"You can no longer use the current version. <br><br>" \
                  u"Please download the latest version (zip file) from <a href='{url}'>{url}</a>. " \
                  u"Installation instructions can be found in the README.md file at the same location.<br><br>" \
                  u"This application will now exit.".format(url=package_url)
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Information)
            msg.setText(txt)
            msg.setTextFormat(QtCore.Qt.RichText)
            msg.setWindowTitle(u"New version available!")
            msg.exec_()
            sys.exit()

    def clearSelection(self):
        selection = self.tableViewData.selectionModel()
        selectionRange = selection.selection()
        selection.select(selectionRange, QtGui.QItemSelectionModel.Clear)

    def copy(self):
        """Implements Excel-style copy."""
        # Find the selected cells
        selection = self.tableViewData.selectionModel()
        indexes = selection.selectedIndexes()
        if len(indexes) < 1:
            # Nothing selected
            return None

        # Start copying
        text = ''
        rows = [r.row() for r in indexes]
        cols = [c.column() for c in indexes]
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                item = self.sampleModel.data(self.sampleModel.index(r, c))
                text += item
                if c != max(cols):
                    text += '\t'
            if r != max(rows):
                text += '\n'
        QtGui.QApplication.clipboard().setText(text)
        return rows, cols

    def cut(self):
        """Implements Excel-style cut."""
        # Copy the selected cells
        rows, cols = self.copy()
        # Prepare the undo macro
        self.undoStack.beginMacro("Cut data")
        # Begin cut operations
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                index = self.sampleModel.index(r, c)
                value = QtCore.QString("")
                previous = self.sampleModel.data(index)
                command = CommandSetData(self.sampleModel, index, value, previous)
                self.undoStack.push(command)
        self.undoStack.endMacro()

    def delete(self):
        """Deletes data from currently selected cells."""
        # Find the selected cells
        selection = self.tableViewData.selectionModel()
        indexes = selection.selectedIndexes()
        if len(indexes) < 1:
            # Nothing selected
            return None

        # Prepare undo macro
        self.undoStack.beginMacro("Delete data")
        # Start deleting
        for i in indexes:
            value = QtCore.QString("")
            previous = self.sampleModel.data(i)
            command = CommandSetData(self.sampleModel, i, value, previous)
            self.undoStack.push(command)
        self.undoStack.endMacro()

        return  None

    def delRows(self):
        """Deletes selected rows from the table."""
        rows = self.tableViewData.selectionModel().selectedRows()
        # Reverse the order of rows so we delete from the bottom up
        # to avoid errors.
        rows.reverse()
        # TODO: implement undo here
        for row in rows:
            self.sampleModel.removeRow(row.row())

    def exportData(self):
        """Exports data to csv file."""
        dataValid, txt = self.validateExport()
        if not dataValid:
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(txt)
            msg.setWindowTitle(u"Data validation - errors detected!")
            msg.exec_()
            return None

        # If the data is valid, keep going with the export.
        fileName = QtGui.QFileDialog.getSaveFileName(caption=u'Save file', selectedFilter=u'*.csv')

        # Take a row and append each item to a list.
        tableData = []
        for row in range(self.sampleModel.rowCount()):
            tableData.append([])
            for column in range(self.sampleModel.columnCount()):
                index = self.sampleModel.index(row, column)
                tableData[row].append(str(self.sampleModel.data(index)))
        # Transform the list to a dictionary for dictWriter
        tableData = functions.lorl2lord(tableData, app_config['column_order'])
        # Reformat the data in parameter-oriented format
        data_reformatted = functions.prepare_dictionary(tableData, 'YYYY-MM-DD')
        # Prepare the message box for confirmation after export
        msg = QtGui.QMessageBox()
        # Write the data to csv
        try:
            # Write to sample oriented file for QA
            if self.chkBoxSampleOriented.isChecked():
                fn = os.path.splitext(str(fileName))[0] + '_sampleOriented' + '.csv'
                functions.write_to_csv(tableData, fn, app_config['column_order'])
            # Write to parameter oriented file for import to KiWQM
            if functions.write_to_csv(data_reformatted, fileName, app_config['csv_fieldnames']):
                msg.setIcon(QtGui.QMessageBox.Information)
                msg.setText(u"Data exported successfully!")
                msg.setWindowTitle(u"Export successful!")
                msg.exec_()
                return None
        except IOError:
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(u"There was an error exporting your file.")
            msg.setWindowTitle(u"Export error!")
            msg.exec_()
            return None

    def filePicker(self):
        """Shows file picker dialog and name in text box."""
        self.fileLineEdit.setText(QtGui.QFileDialog.getOpenFileName())

    def fillSampleLocation(self):
        """Convenience function to fill the selected rows sample and location numbers with ones."""
        # Get the selected cell or cells
        selection = self.tableViewData.selectionModel()
        indexes = selection.selectedIndexes()
        # Get the location of the top left cell in selection
        fillStartRow = min(r.row() for r in indexes)
        fillEndRow = max(r.row() for r in indexes)
        if len(indexes) < 1:
            # Nothing selected
            return None

        # Prepare undo macro
        self.undoStack.beginMacro("Fill sample and location")
        for i in range(fillStartRow, fillEndRow + 1):
            indexLocation = self.sampleModel.createIndex(i, functions.get_column_number('location_id'))
            indexSample = self.sampleModel.createIndex(i, functions.get_column_number('sample_cid'))
            previousLocation = self.sampleModel.data(indexLocation)
            previousSample = self.sampleModel.data(indexSample)
            command = CommandSetData(self.sampleModel, indexLocation, 1, previousLocation)
            self.undoStack.push(command)
            command = CommandSetData(self.sampleModel, indexSample, 1, previousSample)
            self.undoStack.push(command)
        self.undoStack.endMacro()

        return None

    def insertRows(self):
        """Inserts additional rows to the table instance."""
        try:
            rows = self.tableViewData.selectionModel().selectedRows()
            position = rows[0].row()
            rowCount = len(rows)
        except IndexError:
            position = self.sampleModel.rowCount()
            rowCount = 1

        self.sampleModel.insertRows(position, rowCount)

    def keyPressEnter(self):
        """Sets the action of pressing Enter to move the selection to the next row down."""
        currentIndex = self.tableViewData.currentIndex()
        self.tableViewData.setCurrentIndex(self.sampleModel.index(currentIndex.row() + 1, currentIndex.column()))

    def paste(self):
        """Creates Excel-style paste into the table instance from the clipboard."""
        # Get the selected cell or cells
        selection = self.tableViewData.selectionModel()
        indexes = selection.selectedIndexes()
        # Get the location of the top left cell in selection
        pasteStartRow = min(r.row() for r in indexes)
        pasteStartCol = min(c.column() for c in indexes)
        pasteEndRow = max(r.row() for r in indexes)
        pasteEndCol = max(c.column() for c in indexes)
        if len(indexes) < 1:
            # Nothing selected
            return None

        # Excel places an extra newline at the end of everything copied to the
        # clipboard. To ensure we do not lose data, and to ensure consistency
        # we remove any extra newline characters from the end of the text.
        txt = QtGui.QApplication.clipboard().text()
        if txt.endsWith('\n'):
            txt.chop(1)

        # Parse the clipboard
        copyDataRows = txt.split('\n')
        if copyDataRows is None:
            # Nothing in the clipboard
            return None

        # Paste data
        # Special case - only one value selected
        if len(copyDataRows) == 1 and '\t' not in copyDataRows[0]:
            copyData = copyDataRows[0]
            for i in range(pasteEndRow - pasteStartRow + 1):
                for j in range(pasteEndCol - pasteStartCol + 1):
                    index = self.sampleModel.index(pasteStartRow + i, pasteStartCol + j)
                    previous = self.sampleModel.data(index)
                    command = CommandSetData(self.sampleModel, index, copyData,
                                             previous, dateFormat=self.dateFormatComboBox.currentText())
                    self.undoStack.push(command)
        else:
            # Prepare the undo macro
            self.undoStack.beginMacro("Paste data")
            # Paste data in rows, starting from top and moving left to right
            for i in range(len(copyDataRows)):
                copyDataCols = copyDataRows[i].split('\t')
                for j in range(len(copyDataCols)):
                    index = self.sampleModel.index(pasteStartRow + i, pasteStartCol + j)
                    previous = self.sampleModel.data(index)
                    command = CommandSetData(self.sampleModel, index, copyDataCols[j],
                                             previous, dateFormat=self.dateFormatComboBox.currentText())
                    self.undoStack.push(command)
            self.undoStack.endMacro()

        return None

    def redo(self):
        self.undoStack.redo()

    def resetData(self):
        """Resets all data in the table instance after confirming with the user."""
        txt = u"All data will be lost. Are you sure you want to continue?"
        msg = QtGui.QMessageBox()
        msg.setIcon(QtGui.QMessageBox.Warning)
        msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        msg.setDefaultButton(QtGui.QMessageBox.Cancel)
        msg.setWindowTitle(u"Warning! Data reset!")
        msg.setText(txt)
        retVal = msg.exec_()
        if retVal == QtGui.QMessageBox.Ok:
            self.sampleModel.resetData()
            self.listWidgetCurrentFiles.clear()
            return None
        else:
            return None

    def selectionChanged(self):
        self.sampleModel.layoutChanged.emit()

    def showAbout(self):
        """Displays the about box from the help menu."""
        aboutMsgBox = QtGui.QMessageBox()
        title = u"FDF Utility v%s" % __version__
        text = u"FDF Utility - an application to format water quality field data " \
               u"for import to KISTERS Water Quality Module (KiWQM) water quality database.\n\n" \
               u"Author: %s\n\nVersion: %s\n\n" \
               u"(C) 2016 New South Wales Department of Industry\n\n" \
               u"For further information, contact the Data & Procedures Officer at DPI Water." \
               % (__author__, __version__)
        aboutMsgBox.about(self, title, text)

    def showHelp(self):
        """Displays the HTML help documentation."""
        self.helpBrowser.show()

    def swapDayMonth(self):
        """Swap the day and month values of selected indices."""
        self.sampleModel.swapMonthDay(self.tableViewData.selectedIndexes())

    def undo(self):
        self.undoStack.undo()

    def updateGlobalFrozenColumns(self, frozenColumns):
        """Update the number of frozen columns at the left of the table."""
        settings.FROZEN_COLUMNS = frozenColumns

    def validateExport(self):
        """Validates the table data for completeness and for fitting to business rules"""
        dataValid = True
        model = self.sampleModel
        rows = model.rowCount()
        columns = model.columnCount()

        # Test for presence of data
        if rows == 0:
            dataValid = False
            msg = u"There is no data to export! Please add data and try again."
            return dataValid, msg

        # Test for red cells (previously validated)
        invalidColumns = []
        for i in range(columns):
            for j in range(rows):
                index = model.index(j, i)
                if model.data(index, role=QtCore.Qt.BackgroundRole) == QtGui.QBrush(QtCore.Qt.red):
                    invalidColumns.append(i)
                    break

        # Test for incomplete required fields
        incompleteColumns = []
        for i in range(columns):
            for j in range(rows):
                index = model.index(j, i)
                if model.data(index) == "":
                    if model.data(model.index(j, functions.get_column_number('sample_collected'))) == "NO":
                        if column_config[i]['required_if_not_sampled']:
                            incompleteColumns.append(i)
                            break
                    else:
                        if column_config[i]['required']:
                            incompleteColumns.append(i)
                            break

        # Test matrix consistency
        matrixConsistent = model.checkMatrixConsistency()

        # Test sequence number validity
        sequenceCorrect = model.checkSequenceNumbers()

        # Prepare message for user
        msg = u""
        if invalidColumns:
            dataValid = False
            listOfColumnNames = u'\n'.join(column_config[k]['display_name'] for k in invalidColumns)
            msg += u"The following columns have invalid values:\n" + listOfColumnNames

        if incompleteColumns:
            dataValid = False
            listOfColumnNames = u'\n'.join(column_config[k]['display_name'] for k in incompleteColumns)
            if msg:
                msg += u"\n\n"
            msg += u"The following required columns have one or more empty values:\n" + listOfColumnNames
            if 'Comments' in listOfColumnNames:
                msg += u"\n\nA comment must be included for all samples tagged as not sampled."

        if not matrixConsistent:
            dataValid = False
            if msg:
                msg += u"\n\n"
            msg += u"Matrix errors detected:\n" \
                   u"More than one matrix has been defined for a single sampling event.\n" \
                   u"Please ensure that only a single matrix is used for all samples in a " \
                   u"sampling event (for primary and replicates) before exporting."

        if not sequenceCorrect:
            dataValid = False
            if msg:
                msg += u"\n\n"
            msg += u"Sequence number errors detected:\nOne or more problems have been " \
                   u"detected with the provided sequence numbers. Please ensure that:\n" \
                   u"- All samples in a single sampling event use distinct sequence numbers;\n" \
                   u"- The first sample in all sampling events is 1;\n" \
                   u"- All sequence numbers in a single sampling event increment sequentially." \
                   u"\nA sampling event consists of all samples collected at the same station " \
                   u"on the same date."

        return dataValid, msg


##############################################################################
# Main application
##############################################################################
def main():
    """
    Run the Field Data Formatter app
    """
    app = QtGui.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
