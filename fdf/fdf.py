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

import datetime
import os
import sys
import urllib2

import yaml
from PyQt4 import QtGui, QtCore

import fdfGui
import functions
from functions import DatetimeError, ValidityError
from configuration import app_config, column_config

__author__ = 'Daniel Harris'
__date__ = '27 October 2016'
__email__ = 'daniel.harris@dpi.nsw.gov.au'
__status__ = 'Production'
__version__ = '0.9.1'


###############################################################################
# Main app constructor and initialisation
###############################################################################
class MainApp(fdfGui.Ui_MainWindow, QtGui.QMainWindow):
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

        # Add items to the instrument picker
        instruments = ['']
        instruments.extend(app_config['sources']['hydrolab'])
        instruments.extend(app_config['sources']['ysi'])
        self.instrumentComboBox.addItems(instruments)

        # Set up the table
        self.headerLabels = [column_config[i]['display_name'] for i in range(0, len(column_config))]
        table = self.tableWidgetData
        table.setColumnCount(len(self.headerLabels))
        self.setHeaderData(table)
        table.setItemDelegate(ListColumnItemDelegate())
        table.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed | QtGui.QAbstractItemView.DoubleClicked)
        table.itemChanged.connect(self.autoUpdateCols)
        table.itemChanged.connect(self.validateInput)
        table.itemChanged.connect(self.setAlignment)

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
            menu.addAction(u"Paste", self.paste, QtGui.QKeySequence.Paste)
            menu.popup(QtGui.QCursor.pos())

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.copy()
        elif event.matches(QtGui.QKeySequence.Paste):
            self.paste()
        elif event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.keyPressEnter()
        else:
            QtGui.QMainWindow.keyPressEvent(self, event)

    ##########################################################################
    # Private methods
    ##########################################################################
    def addData(self, lists):
        """Takes data provided and add to the table instance."""
        self.tableWidgetData.blockSignals(True)
        errorsFound = False

        for i in range(0, len(lists)):
            rowPosition = self.tableWidgetData.rowCount()
            self.tableWidgetData.insertRow(rowPosition)
            for j in range(0, len(lists[i])):
                value = str(lists[i][j])
                self.tableWidgetData.setItem(rowPosition, j, QtGui.QTableWidgetItem(value))
                item = self.tableWidgetData.item(rowPosition, j)
                try:
                    validator = DoubleFixupValidator(item.column())
                    state, displayValue, returnInt = validator.validate(item.text(), 0)
                    if state == QtGui.QValidator.Invalid:
                        item.setBackgroundColor(QtCore.Qt.red)
                        errorsFound = True
                except KeyError:
                    pass

        # Update alignment for all cells
        for i in range(0, self.tableWidgetData.rowCount()):
            for j in range(0, self.tableWidgetData.columnCount()):
                self.tableWidgetData.item(i, j).setTextAlignment(QtCore.Qt.AlignCenter)

        if errorsFound:
            txt = u"Errors have been found in the imported data set. " \
                  u"Please check items highlighted in red before exporting."
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(txt)
            msg.setWindowTitle(u"Data import - errors detected!")
            msg.exec_()

        self.tableWidgetData.blockSignals(False)

    def addFile(self):
        """Loads the file specified in the UI and adds it to the table instance."""
        try:
            # Validate file type
            dicts = functions.load_instrument_file(self.fileLineEdit.text(),
                                                   str(self.instrumentComboBox.currentText()))

            # Update sampling number if enough information is in file
            for i in dicts:
                try:
                    i['sampling_number'] = functions.get_sampling_number(
                        station_number=i['station_number'],
                        date=i['date'],
                        sample_type=i['sample_type'])
                except ValueError:
                    pass

            # Add data to table
            self.addData(functions.lord2lorl(dicts, app_config['column_order']))
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

    def autoUpdateCols(self, item):
        """
        Updates the sampling number if the station, date or sampling type
        columns are modified
        """
        table = self.tableWidgetData
        table.blockSignals(True)

        row = item.row()
        col = item.column()
        stationCol = functions.get_column_number('station_number')
        dateCol = functions.get_column_number('date')
        sampleTypeCol = functions.get_column_number('sample_type')
        samplingNumberCol = functions.get_column_number('sampling_number')

        try:
            if col in [stationCol, dateCol, sampleTypeCol]:
                # Get information required for generating the sampling number
                stationNumber = str(table.item(row, stationCol).text())
                date = str(table.item(row, dateCol).text())
                try:
                    sampleType = str(table.item(row, sampleTypeCol).text())
                except AttributeError:
                    sampleType = None

                # Generate the sampling number
                try:
                    samplingNumber = functions.get_sampling_number(
                        station_number=stationNumber,
                        date=date,
                        sample_type=sampleType
                    )
                except ValueError:
                    samplingNumber = ""

                # Set sampling number and correct alignment
                table.setItem(row, samplingNumberCol, QtGui.QTableWidgetItem(samplingNumber))
                self.setAlignment(table.item(row, samplingNumberCol))
        except AttributeError:
            pass
        finally:
            table.blockSignals(False)

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
        selection = self.tableWidgetData.selectionModel()
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
                item = self.tableWidgetData.item(r, c)
                if item:
                    text += item.text()
                if c != max(cols):
                    text += '\t'
            if r != max(rows):
                text += '\n'
        QtGui.QApplication.clipboard().setText(text)

    def delRows(self):
        """Deletes selected rows from the table."""
        rows = self.tableWidgetData.selectionModel().selectedRows()
        # Reverse the order of rows so we delete from the bottom up
        # to avoid errors.
        rows.reverse()
        for r in rows:
            self.tableWidgetData.removeRow(r.row())

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
        for i in range(0, self.tableWidgetData.rowCount()):
            rowData = []
            for j in range(0, self.tableWidgetData.columnCount()):
                value = self.tableWidgetData.item(i, j).text()
                rowData.append(str(value))
            tableData.append(rowData)
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
        table = self.tableWidgetData
        table.blockSignals(True)

        rows = table.selectionModel().selectedRows()
        rowCount = len(rows)
        try:
            rowPosition = rows[0].row()
        except IndexError:
            rowPosition = table.rowCount()
            rowCount = 1
        for i in range(0, rowCount):
            table.insertRow(rowPosition)

        table.blockSignals(False)

    def keyPressEnter(self):
        """Sets the action of pressing Enter to move the selection to the next row down."""
        table = self.tableWidgetData
        item = table.currentItem()
        row = item.row()
        col = item.column()
        # Deselect current item
        table.setItemSelected(table.item(row, col), False)
        # Select next item
        table.setCurrentCell(row + 1, col)

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
            self.tableWidgetData.setRowCount(0)
            self.listWidgetCurrentFiles.clear()
        else:
            return None

    def paste(self):
        """Creates Excel-style paste into the table instance from the clipboard."""
        table = self.tableWidgetData
        table.blockSignals(True)
        # Get the selected cell or cells
        selection = self.tableWidgetData.selectionModel()
        indexes = selection.selectedIndexes()
        # Get the location of the top left cell in selection
        pasteStartRow = min(r.row() for r in indexes)
        pasteStartCol = min(c.column() for c in indexes)
        pasteEndRow = max(r.row() for r in indexes)
        pasteEndCol = max(c.column() for c in indexes)
        if len(indexes) < 1:
            # Nothing selected
            return

        # Parse the clipboard
        copyDataRows = QtGui.QApplication.clipboard().text().split('\n')
        if copyDataRows is None:
            # Nothing in the clipboard
            return

        # Paste data
        # Special case - only one value selected
        if len(copyDataRows) == 1 and '\t' not in copyDataRows[0]:
            copyData = copyDataRows[0]
            for i in range(0, pasteEndRow - pasteStartRow + 1):
                for j in range(0, pasteEndCol - pasteStartCol + 1):
                    table.setItem(pasteStartRow + i,
                                  pasteStartCol + j,
                                  QtGui.QTableWidgetItem(copyData))
                    table.item(pasteStartRow + i, pasteStartCol + j).setTextAlignment(QtCore.Qt.AlignCenter)
                    item = table.item(pasteStartRow + i, pasteStartCol + j)
                    self.autoUpdateCols(item)
        else:
            # Paste data in rows, starting from top and moving left to right
            for i in range(0, len(copyDataRows)):
                copyDataCols = copyDataRows[i].split('\t')
                for j in range(0, len(copyDataCols)):
                    table.setItem(pasteStartRow + i,
                                  pasteStartCol + j,
                                  QtGui.QTableWidgetItem(copyDataCols[j]))
                    try:
                        table.item(pasteStartRow + i, pasteStartCol + j).setTextAlignment(QtCore.Qt.AlignCenter)
                        item = table.item(pasteStartRow + i, pasteStartCol + j)
                        self.autoUpdateCols(item)
                    except AttributeError:
                        pass
        table.blockSignals(False)

    def setHeaderData(self, table):
        """Sets the header labels based on column_config settings."""
        for i in range(0, len(self.headerLabels)):
            item = QtGui.QTableWidgetItem()
            table.setHorizontalHeaderItem(i, item)
            item = table.horizontalHeaderItem(i)
            item.setText(self.headerLabels[i])

    def setAlignment(self, item):
        """Sets alignment for an item."""
        item.setTextAlignment(QtCore.Qt.AlignCenter)

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
        table = self.tableWidgetData
        dataValid = True
        rows = table.rowCount() - 1
        columns = table.columnCount() - 1
        sampleMeasProgColumn = functions.get_column_number('mp_number')
        sampleMatrixColumn = functions.get_column_number('sample_matrix')
        samplingNumberColumn = functions.get_column_number('sampling_number')
        sampleCIDColumn = functions.get_column_number('sample_cid')
        locationNumberColumn = functions.get_column_number('location_id')

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
            if column_config[i]['required']:
                for j in range(0, rows):
                    if table.item(j, i).text() == "":
                        incompleteColumns.append(i)
                    break

        # Test matrix consistency
        matrixConsistent = functions.check_matrix_consistency(
            table, sampleMeasProgColumn, sampleMatrixColumn, samplingNumberColumn
        )

        # Test sequence number validity
        sequenceCorrect = functions.check_sequence_numbers(
            table, sampleMeasProgColumn, sampleCIDColumn,
            samplingNumberColumn, locationNumberColumn
        )

        # Prepare message for user
        msg = u""
        if invalidColumns:
            dataValid = False
            listOfColumnNames = u'\n'.join(column_config[k]['name'] for k in invalidColumns)
            msg += u"The following columns have invalid values:\n" + listOfColumnNames

        if incompleteColumns:
            dataValid = False
            listOfColumnNames = u'\n'.join(column_config[k]['name'] for k in incompleteColumns)
            if not msg:
                msg += u"\n\n"
            msg += u"The following required columns have one or more empty values:\n" + listOfColumnNames

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
        self.tableWidgetData.blockSignals(True)
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
            self.tableWidgetData.blockSignals(False)
            return

        # Validate item
        state, displayValue, returnInt = validator.validate(item.text(), col)
        if state == QtGui.QValidator.Intermediate:
            self.tableWidgetData.blockSignals(False)
            return
        elif state == QtGui.QValidator.Invalid:
            # Prepare message to inform user of invalid value.
            paramName = column_config[col]['name']
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
                txt = "%s value is not a valid value from the drop down list." \
                      "Please select a valid value from the list." % paramName
                windowTitleTxt = "Invalid selection error!"
            elif returnInt == 3:  # Future Date error
                txt = "The entered date is in the future. Sampling dates must be in the past." \
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

        self.tableWidgetData.blockSignals(False)


##############################################################################
# Validator classes
##############################################################################
class DateValidator(QtGui.QValidator):
    def __init__(self):
        super(DateValidator, self).__init__()

    def validate(self, testValue, col):
        try:
            date = functions.parse_datetime_from_string(str(testValue), '00:00:00')
            try:
                displayValue = date.strftime(app_config['datetime_formats']['date']['display'])
            except ValueError:
                # Invalid date error
                displayValue = ""
                state = QtGui.QValidator.Invalid
                returnInt = 4
                return state, displayValue, returnInt
            if date > datetime.datetime.now():
                # Future date error
                state = QtGui.QValidator.Invalid
                returnInt = 3
            else:
                state = QtGui.QValidator.Acceptable
                returnInt = 0
        except DatetimeError:
            # Invalid date error
            displayValue = ""
            state = QtGui.QValidator.Invalid
            returnInt = 4

        return state, displayValue, returnInt


class DoubleFixupValidator(QtGui.QDoubleValidator):
    def __init__(self, column):
        self.column = column
        self.bottom = column_config[self.column]['lower_limit']
        self.top = column_config[self.column]['upper_limit']
        self.decimals = column_config[self.column]['precision']
        super(DoubleFixupValidator, self).__init__(self.bottom, self.top, self.decimals)

    def validate(self, testValue, p_int):
        (state, returnInt) = super(DoubleFixupValidator, self).validate(testValue, p_int)
        if state != QtGui.QValidator.Acceptable:
            # Try to fix the value if possible
            try:
                value = self.fixup(testValue)
                returnInt = 1
                if self.bottom <= value <= self.top:
                    state = QtGui.QValidator.Acceptable
                elif testValue == "":
                    state = QtGui.QValidator.Intermediate
                    value = testValue
                    returnInt = 0
                else:
                    state = QtGui.QValidator.Invalid
            except ValueError:
                value = testValue
                returnInt = 1
        # Test if column can accept zeroes
        elif all([column_config[self.column]['allow_zero'] is False, float(testValue) == 0]):
            state = QtGui.QValidator.Invalid
            value = testValue
            returnInt = 0
        else:
            value = testValue
            returnInt = 1
        return state, str(value), returnInt

    def fixup(self, input):
        """Rounds value to precision specified in column_config."""
        return round(float(input), self.decimals)


class ListValidator(QtGui.QValidator):
    def __init__(self, column):
        self.column = column
        self.list = column_config[self.column]['list_items']
        super(ListValidator, self).__init__()

    def validate(self, testValue, p_int):
        if testValue not in self.list:
            if self.fixup(testValue) in self.list:
                state = QtGui.QValidator.Acceptable
                value = self.fixup(testValue)
                returnInt = 0
            elif testValue == "":
                state = QtGui.QValidator.Intermediate
                value = testValue
                returnInt = 0
            else:
                state = QtGui.QValidator.Invalid
                value = testValue
                returnInt = 2
        else:
            state = QtGui.QValidator.Acceptable
            value = testValue
            returnInt = 0
        return state, value, returnInt

    def fixup(self, input):
        return str(input).upper()


class TimeValidator(QtGui.QValidator):
    def __init__(self):
        super(TimeValidator, self).__init__()

    def validate(self, testValue, col):
        try:
            time = functions.parse_datetime_from_string('01/01/1900', str(testValue))
            try:
                displayValue = time.strftime(app_config['datetime_formats']['time']['display'])
                state = QtGui.QValidator.Acceptable
                returnInt = 0
            except ValueError:
                # Invalid time error
                displayValue = testValue
                state = QtGui.QValidator.Invalid
                returnInt = 4
        except DatetimeError:
            # Invalid time error
            displayValue = testValue
            state = QtGui.QValidator.Invalid
            returnInt = 4

        return state, displayValue, returnInt


##############################################################################
# Style delegates
##############################################################################
class ListColumnItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self):
        super(ListColumnItemDelegate, self).__init__()

    def createEditor(self, parent, option, index):
        combo = FilteredComboBox(parent)
        try:
            items = ['']
            items.extend(column_config[index.column()]['list_items'])
            combo.addItems(items)
            editor = combo
        except KeyError:
            editor = super(ListColumnItemDelegate, self).createEditor(parent, option, index)

        samplingNumberCol = functions.get_column_number("sampling_number")
        if index.column() == samplingNumberCol:
            editor.setReadOnly(True)

        editor.returnPressed.connect(self.commitAndCloseEditor)

        return editor

    def commitAndCloseEditor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QtGui.QAbstractItemDelegate.NoHint)


##############################################################################
# Widgets
##############################################################################
class FilteredComboBox(QtGui.QComboBox):
    """
    Creates a combo box that filters the available options based on user
    input, in a similar way to jQuery.
    """
    # create returnPressed signal
    returnPressed = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(FilteredComboBox, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)
        # Add a filter model to filter matching items
        self.pFilterModel = QtGui.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())
        # Add a completer, which uses the filter model
        self.completer = QtGui.QCompleter(self.pFilterModel, self)
        # Always show all (filtered) completions
        self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        # Connect signals
        def filter(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited[unicode].connect(filter)
        self.completer.activated.connect(self.onCompleterActivated)

    # On selection of an item from the completer, select the corresponding item from combobox
    def onCompleterActivated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)
            self.returnPressed.emit()


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
