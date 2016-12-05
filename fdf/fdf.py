"""
Module: fdf.py
Runs the KiWQM Field Data Formatter GUI, used to generate a valid
field data import file for KiWQM.

Author: Daniel Harris
Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 27/09/2016

External dependencies: PyYAML, PyQT4

Classes:
MainApp: Constructor for the main application.
DateValidator: Validator for dates
DoubleFixupValidator: Validator for doubles
FilteredComboBox: Drop-down jQuery-style filtered combo-box
ListColumnItemDelegate: Style delegate for list columns
ListValidator: Validator for list items
TimeValidator: Validator for times

Functions:
Main: Runs the Field Data Formatter app.
"""

# Standard library imports
import datetime
import os
import sys
import urllib2

# Related third party imports
import yaml
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot

# Local application imports
import fdfGui2
import functions
from functions import DatetimeError, ValidityError
from configuration import app_config, column_config
from delegates import tableDelegate

__author__ = 'Daniel Harris'
__date__ = '4 November 2016'
__email__ = 'daniel.harris@dpi.nsw.gov.au'
__status__ = 'Development'
__version__ = '0.9.6'


###############################################################################
# Models
###############################################################################
class tableModel(QtCore.QAbstractTableModel):
    # table.setItemDelegate(ListColumnItemDelegate())
    # table.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed | QtGui.QAbstractItemView.DoubleClicked)

    def __init__(self, samples=[], headers=[], parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._samples = samples
        self.__headers = headers

        if not self._samples:
            self._samples.append(self.defaultData())

    def rowCount(self, parent=None):
        return len(self._samples)

    def columnCount(self, parent=None):
        return len(column_config)

    def flags(self, index):
        if index.column() == functions.get_column_number('sampling_number'):
            flags = QtCore.Qt.ItemIsEnabled
        else:
            flags = QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return flags

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        column = index.column()
        value = self._samples[row][column]

        if role == QtCore.Qt.DisplayRole:
            if type(value) in (QtCore.QDate, QtCore.QTime):
                value = value.toString(QtCore.Qt.ISODate)
            if value and 'lower_limit' in column_config[column]:
                value = QtCore.QString.number(value, 'f', column_config[column]['precision'])
            return value

        if role == QtCore.Qt.EditRole:
            return value

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid() and role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()

            # Update sampling number
            if column == functions.get_column_number('date'):
                try:
                    sampling_number = functions.get_sampling_number(
                        station_number=self._samples[row][functions.get_column_number('station_number')],
                        date=value.toString(),
                        sample_type=self._samples[row][functions.get_column_number('sample_type')]
                    )
                    self._samples[row][functions.get_column_number('sampling_number')] = sampling_number
                    idxChanged = self.createIndex(
                        row, functions.get_column_number('sampling_number')
                    )
                    self.dataChanged.emit(idxChanged, idxChanged)
                except ValueError:
                    pass

            if column == functions.get_column_number('sample_type'):
                try:
                    sampling_number = functions.get_sampling_number(
                        station_number=self._samples[row][functions.get_column_number('station_number')],
                        date=self._samples[row][functions.get_column_number('date')].toString(),
                        sample_type=value
                    )
                    self._samples[row][functions.get_column_number('sampling_number')] = sampling_number
                    idxChanged = self.createIndex(
                        row, functions.get_column_number('sampling_number')
                    )
                    self.dataChanged.emit(idxChanged, idxChanged)
                except ValueError:
                    pass

            # TODO: can probably get rid of this bit
            if value and 'lower_limit' in column_config[column]:
                value = float(value)

            if column in [functions.get_column_number('latitude'), functions.get_column_number('longitude')]:
                try:
                    if column == functions.get_column_number('latitude'):
                        if value > 0:
                            value *= -1
                        latitude = value
                        longitude = self.data(self.createIndex(row, functions.get_column_number('longitude')), QtCore.Qt.EditRole)
                    else:
                        latitude = self.data(self.createIndex(row, functions.get_column_number('latitude')), QtCore.Qt.EditRole)
                        longitude = value

                    # Calculate MGA94 coordinates
                    easting, northing, map_zone = functions.get_mga_coordinates(latitude, longitude)

                    # Set MGA94 coordinates
                    self._samples[row][functions.get_column_number('easting')] = easting
                    idxChanged = self.createIndex(row, functions.get_column_number('easting'))
                    self.dataChanged.emit(idxChanged, idxChanged)

                    self._samples[row][functions.get_column_number('northing')] = northing
                    idxChanged = self.createIndex(row, functions.get_column_number('northing'))
                    self.dataChanged.emit(idxChanged, idxChanged)

                    self._samples[row][functions.get_column_number('map_zone')] = map_zone
                    idxChanged = self.createIndex(row, functions.get_column_number('map_zone'))
                    self.dataChanged.emit(idxChanged, idxChanged)
                except ValueError:
                    pass

            self._samples[row][column] = value
            self.dataChanged.emit(index, index)
            return True

        return False

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return column_config[section]['display_name']
            else:
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

    def resetData(self):
        for i in range(self.rowCount(), 0, -1):
            self.removeRow(i - 1)

    def defaultData(self):
        defaultValues = [QtCore.QString("") for column in range(len(column_config))]
        defaultValues[functions.get_column_number('date')] = QtCore.QDate()
        defaultValues[functions.get_column_number('time')] = QtCore.QTime()
        return defaultValues

###############################################################################
# Main app constructor and initialisation
###############################################################################
class MainApp(fdfGui2.Ui_MainWindow, QtGui.QMainWindow):
    """
    Constructor for the main application
    """
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.checkVersion()
        self.setupUi(self)
        self.filePickerBtn.clicked.connect(self.filePicker)
        self.addFileBtn.clicked.connect(self.addFile)
        self.pushButtonDeleteLines.clicked.connect(self.delRows)
        self.pushButtonAddLines.clicked.connect(self.insertRows)
        self.pushButtonResetData.clicked.connect(self.resetData)
        self.pushButtonExportData.clicked.connect(self.exportData)

        # Set up model
        # Create empty dicionary to go in as first value
        self.sampleModel = tableModel()
        self.tableViewData.setModel(self.sampleModel)
        self.tableViewData.setItemDelegate(tableDelegate())
        self.sampleModel.removeRows(0, 1)

        # Add items to the instrument picker
        instruments = ['']
        instruments.extend(app_config['sources']['hydrolab'])
        instruments.extend(app_config['sources']['ysi'])
        self.instrumentComboBox.addItems(instruments)

        # Set up the help documentation
        self.helpBrowser = QtGui.QTextBrowser()
        self.helpBrowser.setSource(QtCore.QUrl('help.html'))
        self.helpBrowser.setWindowTitle(u"FDF Utility Help Documentation")
        self.helpBrowser.setMinimumSize(500, 500)
        self.actionHelp.triggered.connect(self.showHelp)

        # Set up the about documentation
        self.actionAbout.triggered.connect(self.showAbout)

    ##########################################################################
    # Reimplemented methods
    ##########################################################################
    def contextMenuEvent(self, event):
        if event.Reason() == QtGui.QContextMenuEvent.Mouse:
            menu = QtGui.QMenu(self)
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
        elif event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.keyPressEnter()
        else:
            QtGui.QMainWindow.keyPressEvent(self, event)

    ##########################################################################
    # Private methods
    ##########################################################################
    def addFile(self):
        """Loads the file specified in the UI and adds it to the table instance."""
        try:
            # Validate file type
            dicts = functions.load_instrument_file(self.fileLineEdit.text(),
                                                   str(self.instrumentComboBox.currentText()))

            # Add data to table
            lists = functions.lord2lorl(dicts, app_config['column_order'])

            self.sampleModel.insertRows(self.sampleModel.rowCount(), len(lists))
            for i in range(len(lists)):
                date = lists[i][functions.get_column_number('date')]
                time = lists[i][functions.get_column_number('time')]
                dt = functions.parse_datetime_from_string(date, time)
                for j in range(len(lists[i])):
                    if j == functions.get_column_number('date'):
                        lists[i][j] = QtCore.QDate(dt.year, dt.month, dt.day)
                    if j == functions.get_column_number('time'):
                        lists[i][j] = QtCore.QTime(dt.hour, dt.minute, dt.second)
                    self.sampleModel.setData(self.sampleModel.index(i, j), lists[i][j])

            # Add file name to listbox
            self.listWidgetCurrentFiles.addItem(QtGui.QListWidgetItem(self.fileLineEdit.text()))

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

    def copy(self):
        """Implements Excel-style copy."""
        # Find the selected cells
        selection = self.tableViewData.selectionModel()
        indexes = selection.selectedIndexes()
        if len(indexes) < 1:
            # Nothing selected
            return

        # Start copying
        text = ''
        rows = [r.row() for r in indexes]
        cols = [c.column() for c in indexes]
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                item = self.sampleModel.data(self.sampleModel.createIndex(r, c))
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
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                self.sampleModel.setData(self.sampleModel.createIndex(r, c), QtCore.QString(""))

    def delete(self):
        """Deletes data from currently selected cells."""
        # Find the selected cells
        selection = self.tableViewData.selectionModel()
        indexes = selection.selectedIndexes()
        if len(indexes) < 1:
            # Nothing selected
            return

        # Start deleting
        for i in indexes:
            self.sampleModel.setData(i, QtCore.QString(""))

    def delRows(self):
        """Deletes selected rows from the table."""
        rows = self.tableViewData.selectionModel().selectedRows()
        # Reverse the order of rows so we delete from the bottom up
        # to avoid errors.
        rows.reverse()
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
        data_reformatted = functions.prepare_dictionary(tableData)
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
        self.tableViewData.setCurrentIndex(self.sampleModel.createIndex(currentIndex.row() + 1, currentIndex.column()))

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
        else:
            return None

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
            return

        # Paste data
        # Special case - only one value selected
        if len(copyDataRows) == 1 and '\t' not in copyDataRows[0]:
            copyData = copyDataRows[0]
            for i in range(pasteEndRow - pasteStartRow + 1):
                for j in range(pasteEndCol - pasteStartCol + 1):
                    self.sampleModel.setData(self.sampleModel.createIndex(pasteStartRow + i, pasteStartCol + j), copyData)
        else:
            # Paste data in rows, starting from top and moving left to right
            for i in range(len(copyDataRows)):
                copyDataCols = copyDataRows[i].split('\t')
                for j in range(len(copyDataCols)):
                    self.sampleModel.setData(self.sampleModel.createIndex(pasteStartRow + i, pasteStartCol + j), copyDataCols[j])

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

    def validateExport(self):
        """Validates the table data for completeness and for fitting to business rules"""
        table = self.tableViewData
        dataValid = True
        rows = table.rowCount()
        columns = table.columnCount()
        sampleMeasProgColumn = functions.get_column_number('mp_number')
        sampleMatrixColumn = functions.get_column_number('sample_matrix')
        samplingNumberColumn = functions.get_column_number('sampling_number')
        sampleCIDColumn = functions.get_column_number('sample_cid')
        locationNumberColumn = functions.get_column_number('location_id')
        sampleCollectedColumn = functions.get_column_number('sample_collected')

        # Test for presence of data
        if rows <= 0:
            dataValid = False
            msg = u"There is no data to export! Please add data and try again."
            return dataValid, msg

        # Test for red cells (previously validated)
        invalidColumns = []
        for i in range(0, columns):
            for j in range(0, rows):
                if table.item(j, i).backgroundColor() == QtCore.Qt.red:
                    invalidColumns.append(i)
                    break

        # Test for incomplete required fields
        incompleteColumns = []
        for i in range(0, columns):
            for j in range(0, rows):
                if table.item(j, i).text() == "":
                    if table.item(j, sampleCollectedColumn).text() == "No":
                        if column_config[i]['required_if_not_sampled']:
                            incompleteColumns.append(i)
                            break
                    else:
                        if column_config[i]['required']:
                            incompleteColumns.append(i)
                            break

        # Test matrix consistency
        matrixConsistent = functions.check_matrix_consistency(
            table, sampleMeasProgColumn, sampleMatrixColumn, samplingNumberColumn
        )

        # Test sequence number validity
        sequenceCorrect = functions.check_sequence_numbers(
            table, sampleMeasProgColumn, sampleCIDColumn,
            samplingNumberColumn, locationNumberColumn,
            sampleCollectedColumn
        )

        # Prepare message for user
        msg = u""
        if invalidColumns:
            dataValid = False
            listOfColumnNames = u'\n'.join(column_config[k]['display_name'] for k in invalidColumns)
            msg += u"The following columns have invalid values:\n" + listOfColumnNames

        if incompleteColumns:
            dataValid = False
            listOfColumnNames = u'\n'.join(column_config[k]['display_name'] for k in incompleteColumns)
            if not msg:
                msg += u"\n\n"
            msg += u"The following required columns have one or more empty values:\n" + listOfColumnNames
            if 'Comments' in listOfColumnNames:
                msg += u"\n\nA comment must be included for all samples tagged as not sampled."

        if not matrixConsistent:
            dataValid = False
            if not msg:
                msg += u"\n\n"
            msg += u"Matrix errors detected:\n" \
                   u"More than one matrix has been defined for a single sampling event.\n" \
                   u"Please ensure that only a single matrix is used for all samples in a " \
                   u"sampling event (for primary and replicates) before exporting."

        if not sequenceCorrect:
            dataValid = False
            if not msg:
                msg += u"\n\n"
            msg += u"Sequence number errors detected:\nOne or more problems have been " \
                   u"detected with the provided sequence numbers. Please ensure that:\n" \
                   u"- All samples in a single sampling event use distinct sequence numbers;\n" \
                   u"- The first sample in all sampling events is 1;\n" \
                   u"- All sequence numbers in a single sampling event increment sequentially." \
                   u"\nA sampling event consists of all samples collected at the same station " \
                   u"on the same date."

        return dataValid, msg

    def validateInput(self, item):
        """Validates the input of data to a cell."""
        self.tableViewData.blockSignals(True)
        col = item.column()

        # Select correct validator
        if column_config[col]['name'] == 'date':
            validator = DateValidator()
        elif column_config[col]['name'] == 'time':
            validator = TimeValidator()
        elif 'list_items' in column_config[col]:
            validator = ListValidator(col)
        elif 'lower_limit' in column_config[col]:
            validator = DoubleFixupValidator(col)
        else:
            self.tableViewData.blockSignals(False)
            return

        # Validate item
        state, displayValue, returnInt = validator.validate(item.text(), col)
        if state == QtGui.QValidator.Intermediate:
            self.tableViewData.blockSignals(False)
            return
        elif state == QtGui.QValidator.Invalid:
            # Prepare message to inform user of invalid value.
            paramName = column_config[col]['display_name']
            item.setText(displayValue)
            item.setBackgroundColor(QtCore.Qt.red)
            if returnInt == 0:  # Zero-error
                txt = "%s value has a value of zero (0).\n" \
                      "A value of zero generally indicates a sensor failure, or a non-measured parameter.\n" \
                      "Please review and adjust before continuing." % paramName
                windowTitleTxt = "Data quality error!"
            elif returnInt == 1:  # Data range error
                lowerLimit = column_config[col]['lower_limit']
                upperLimit = column_config[col]['upper_limit']
                txt = "%s value out of range.\n Acceptable range is between %s and %s" % (paramName, lowerLimit, upperLimit)
                windowTitleTxt = "Value range error!"
            elif returnInt == 2:  # List error
                txt = "%s value is not a valid value from the drop down list.\n" \
                      "Please select a valid value from the list." % paramName
                windowTitleTxt = "Invalid selection error!"
            elif returnInt == 3:  # Future Date error
                txt = "The entered date is in the future. Sampling dates must be in the past.\n" \
                      "Please enter a different date."
                windowTitleTxt = "Invalid date error!"
            else:  # returnInt == 4  # Date/time format error
                txt = "The entered time or date is invalid. Please enter a valid date/time."
                windowTitleTxt = "Invalid date/time error!"

            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(txt)
            msg.setWindowTitle(windowTitleTxt)
            msg.exec_()
        else:  # Valid value
            item.setText(displayValue)
            item.setBackgroundColor(QtCore.Qt.white)

        self.tableViewData.blockSignals(False)


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
