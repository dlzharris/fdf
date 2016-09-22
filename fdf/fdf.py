"""
Module: mainapp.py
Runs the KiWQM Field Data Formatter GUI, used to generate a valid
field data import file for KiWQM.

Author: Daniel Harris
Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/10/2015

Classes:
MainApp: Constructor for the main application.

Functions:
Main: Runs the Field Data Formatter app.
"""
__version__ = '0.9.0'
# TODO: Code clean and document

import sys
import os
from PyQt4 import QtGui, QtCore
import fdfGui
import functions
from functions import DatetimeError, ValidityError
import yaml
import datetime
import urllib2

# Load config files
#column_config = yaml.load(open(functions.resource_path('column_config.yaml')).read())
#app_config = yaml.load(open(functions.resource_path('app_config.yaml')).read())
column_config = yaml.load(open('column_config.yaml').read())
app_config = yaml.load(open('app_config.yaml').read())


###############################################################################
# Main app constructor and initialisation
###############################################################################
class MainApp(fdfGui.Ui_MainWindow, QtGui.QMainWindow):
    """
    Constructor for the main application
    """
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self._checkVersion()
        self.setupUi(self)
        self.filePickerBtn.clicked.connect(self._filePicker)
        self.addFileBtn.clicked.connect(self._addFile)
        self.pushButtonDeleteLines.clicked.connect(self._delRows)
        self.pushButtonAddLines.clicked.connect(self._insertRows)
        self.pushButtonResetData.clicked.connect(self._resetData)
        self.pushButtonExportData.clicked.connect(self._exportData)
        # Add items to the instrument picker
        instrumentCol = functions.get_column_number('sampling_instrument')
        _instruments = ['']
        _instruments.extend(column_config[instrumentCol]['list_items'])
        self.instrumentComboBox.addItems(_instruments)
        # Set up the table
        self.headerLabels = [column_config[i]['display_name'] for i in range(0, len(column_config))]
        table = self.tableWidgetData
        table.setColumnCount(len(self.headerLabels))
        self.setHeaderData(table)
        table.setItemDelegate(listColumnItemDelegate())
        table.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed | QtGui.QAbstractItemView.DoubleClicked)
        table.itemChanged.connect(self._autoUpdateCols)
        table.itemChanged.connect(self._validateInput)
        table.itemChanged.connect(self._setAlignment)
        # Set up the help documentation
        self.helpBrowser = QtGui.QTextBrowser()
        self.helpBrowser.setSource(QtCore.QUrl('help.html'))
        self.helpBrowser.setWindowTitle("FDF Utility Help Documentation")
        self.helpBrowser.setMinimumSize(500, 500)
        self.actionHelp.triggered.connect(self._showHelp)

    def _checkVersion(self):
        try:
            # Check that version is up-to-date
            version_url = 'https://raw.githubusercontent.com/dlzharris/fdf/master/current_version.txt'
            package_url = 'https://github.com/dlzharris/fdf/tree/master/stable_package'
            proxy = urllib2.ProxyHandler({'http': 'oranprodproxy.dpi.nsw.gov.au:8080',
                                          'https': 'oranprodproxy.dpi.nsw.gov.au:8080'})
            opener = urllib2.build_opener(proxy)
            urllib2.install_opener(opener)
            current_version = yaml.load(urllib2.urlopen(version_url).read())['version_stable']
            if __version__ != current_version:
                txt = "There is a newer version of this application available. " \
                      "You can no longer use the current version. <br><br>" \
                      "Please download the latest version (zip file) from <a href='{url}'>{url}</a>. " \
                      "Installation instructions can be found in the README.md file at the same location.<br><br>" \
                      "This application will now exit.".format(url=package_url)
                msg = QtGui.QMessageBox()
                msg.setIcon(QtGui.QMessageBox.Information)
                msg.setText(txt)
                msg.setTextFormat(QtCore.Qt.RichText)
                msg.setWindowTitle("New version available!")
                msg.exec_()
                sys.exit()
        except urllib2.URLError:
            return

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self._copy()
        elif event.matches(QtGui.QKeySequence.Paste):
            self._paste()
        elif event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self._keyPressEnter()
        else:
            QtGui.QMainWindow.keyPressEvent(self, event)

    def contextMenuEvent(self, event):
        if event.Reason() == QtGui.QContextMenuEvent.Mouse:
            menu = QtGui.QMenu(self)
            menu.addAction("Copy", self._copy, QtGui.QKeySequence.Copy)
            menu.addAction("Paste", self._paste, QtGui.QKeySequence.Paste)
            menu.popup(QtGui.QCursor.pos())

    def setHeaderData(self, table):
        for i in range(0, len(self.headerLabels)):
            item = QtGui.QTableWidgetItem()
            table.setHorizontalHeaderItem(i, item)
            item = table.horizontalHeaderItem(i)
            item.setText(self.headerLabels[i])

    def _showHelp(self):
        self.helpBrowser.show()

    def _filePicker(self):
        # Show file picker dialog and show name in text box
        self.fileLineEdit.setText(QtGui.QFileDialog.getOpenFileName())

    def _addFile(self):
        try:
            # Validate file type
            _dicts = functions.load_instrument_file(self.fileLineEdit.text(), str(self.instrumentComboBox.currentText()))
            self._addData(functions.lord2lorl(_dicts, app_config['column_order']))
            # Add file name to listbox
            self.listWidgetCurrentFiles.addItem(QtGui.QListWidgetItem(self.fileLineEdit.text()))
        except ValidityError:
            txt = "The chosen file is not valid for the specified instrument.\n\n" \
                  "Please select a different file or a different instrument from the drop-down list."
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(txt)
            msg.setWindowTitle("File validity error!")
            msg.exec_()

    def _addData(self, lists):
        self.tableWidgetData.blockSignals(True)
        errorsFound = False
        for i in range(0, len(lists)):
            rowPosition = self.tableWidgetData.rowCount()
            self.tableWidgetData.insertRow(rowPosition)
            for j in range(0, len(lists[i])):
                value = str(lists[i][j])
                self.tableWidgetData.setItem(rowPosition, j, QtGui.QTableWidgetItem(value))
                item = self.tableWidgetData.item(i, j)
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


        self.tableWidgetData.blockSignals(False)
        if errorsFound is True:
            txt = "Errors have been found in the imported data set. " \
                  "Please check items highlighted in red before exporting."
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(txt)
            msg.setWindowTitle("Data import - errors detected!")
            msg.exec_()

    def _insertRows(self):
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

    def _delRows(self):
        rows = self.tableWidgetData.selectionModel().selectedRows()
        rows.reverse()
        for r in rows:
            self.tableWidgetData.removeRow(r.row())

    def _resetData(self):
        self.tableWidgetData.setRowCount(0)
        self.listWidgetCurrentFiles.clear()

    def _exportData(self):
        dataValid, txt = exportValidator(self.tableWidgetData)
        if not dataValid:
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(txt)
            msg.setWindowTitle("Data validation - errors detected!")
            msg.exec_()
            return None
        # If the data is valid, keep going with the export
        fileName = QtGui.QFileDialog.getSaveFileName(caption='Save file', selectedFilter='*.csv')
        # take a row and append each item to a list
        tableData = []
        for i in range(0, self.tableWidgetData.rowCount()):
            rowData = []
            for j in range(0, self.tableWidgetData.columnCount()):
                value = self.tableWidgetData.item(i, j).text()
                rowData.append(str(value))
            tableData.append(rowData)
        tableData = functions.lorl2lord(tableData, app_config['column_order'])
        # Reformat the data in parameter-oriented format
        data_reformatted = functions.prepare_dictionary(tableData)
        # Write the data to csv
        msg = QtGui.QMessageBox()
        try:
            # Write to sample oriented file for QA
            if self.chkBoxSampleOriented.isChecked():
                fn = os.path.splitext(str(fileName))[0] + '_sampleOriented' + '.csv'
                functions.write_to_csv(tableData, fn, app_config['column_order'])
            # Write to parameter oriented file for import to KiWQM
            if functions.write_to_csv(data_reformatted, fileName, app_config['csv_fieldnames']):
                msg.setIcon(QtGui.QMessageBox.Information)
                msg.setText("Data exported successfully!")
                msg.setWindowTitle("Export successful!")
                msg.exec_()
                return None
        except IOError:
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText("There was an error exporting your file.")
            msg.setWindowTitle("Export error!")
            msg.exec_()

    def _copy(self):
        selection = self.tableWidgetData.selectionModel()
        indexes = selection.selectedIndexes()
        if len(indexes) < 1:
            # Nothing selected
            return
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

    def _paste(self):
        table = self.tableWidgetData
        table.blockSignals(True)
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
                    self._autoUpdateCols(item)
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
                        self._autoUpdateCols(item)
                    except AttributeError:
                        pass
        table.blockSignals(False)

    def _keyPressEnter(self):
        table = self.tableWidgetData
        item = table.currentItem()
        row = item.row()
        col = item.column()
        # Deselect current item
        table.setItemSelected(table.item(row, col), False)
        # Select next item
        table.setCurrentCell(row + 1, col)

    def _autoUpdateCols(self, item):
        table = self.tableWidgetData
        table.blockSignals(True)
        row = item.row()
        col = item.column()
        stationCol = functions.get_column_number('station_number')
        dateCol = functions.get_column_number('date')
        sampleTypeCol = functions.get_column_number('sample_type')
        samplingNumberCol = functions.get_column_number('sampling_number')
        try:
            if col in [stationCol, dateCol]:  # Sampling number
                stationNumber = str(table.item(row, stationCol).text())
                date = str(table.item(row, dateCol).text())

                try:
                    sampleType = str(table.item(row, sampleTypeCol).text())
                except AttributeError:
                    sampleType = None

                try:
                    samplingNumber = functions.get_sampling_number(
                        station_number=stationNumber,
                        date=date,
                        sample_type=sampleType)
                except ValueError:
                    samplingNumber = ""

                table.setItem(row, samplingNumberCol, QtGui.QTableWidgetItem(samplingNumber))
                self._setAlignment(table.item(row, samplingNumberCol))

        except AttributeError:
            pass
        finally:
            table.blockSignals(False)

    def _setAlignment(self, item):
        item.setTextAlignment(QtCore.Qt.AlignCenter)

    def _validateInput(self, item):
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
        elif state != QtGui.QValidator.Acceptable:
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
        else:
            item.setText(displayValue)
            item.setBackgroundColor(QtCore.Qt.white)

        self.tableWidgetData.blockSignals(False)


class DateValidator(QtGui.QValidator):
    def __init__(self):
        super(DateValidator, self).__init__()

    def validate(self, testValue, col):
        try:
            date = functions.parse_datetime_from_string(str(testValue), '00:00:00')
            try:
                displayValue = date.strftime(app_config['datetime_formats']['date']['display'])
            except ValueError:
                displayValue = ""
                state = QtGui.QValidator.Invalid
                returnInt = 4
                return state, displayValue, returnInt
            if date > datetime.datetime.now():
                state = QtGui.QValidator.Invalid
                returnInt = 3
            else:
                state = QtGui.QValidator.Acceptable
                returnInt = 0
        except DatetimeError:
            displayValue = ""
            state = QtGui.QValidator.Invalid
            returnInt = 4

        return state, displayValue, returnInt


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
                displayValue = testValue
                state = QtGui.QValidator.Invalid
                returnInt = 4
        except DatetimeError:
            displayValue = testValue
            state = QtGui.QValidator.Invalid
            returnInt = 4

        return state, displayValue, returnInt


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
        return round(float(input), self.decimals)


def exportValidator(table):
    table = table
    rows = table.rowCount() - 1
    columns = table.columnCount() - 1
    dataValid = True
    sampleMeasProgColumn = functions.get_column_number('mp_number')
    sampleMatrixColumn = functions.get_column_number('sample_matrix')
    samplingNumberColumn = functions.get_column_number('sampling_number')
    sampleCIDColumn = functions.get_column_number('sample_cid')
    locationNumberColumn = functions.get_column_number('location_id')
    # Test for presence of data
    if rows <= 0:
        dataValid = False
        msg = "There is no data to export! Please add data and try again."
        return dataValid, msg
    # Test for red cells (previously validated)
    invalidColumns = []
    for i in range(0, columns):
        for j in range(0, rows):
            if table.item(j, i).backgroundColor() == QtCore.Qt.red:
                invalidColumns.append(i)
                break
    # Test incomplete_fields:
    incompleteColumns = []
    for i in range(0, columns):
        if column_config[i]['required'] is True:
            for j in range(0, rows):
                if table.item(j, i).text() == "":
                    incompleteColumns.append(i)
                break
    # Test matrix consistency
    matrixConsistent = functions.check_matrix_consistency(table, sampleMeasProgColumn,
                                                          sampleMatrixColumn, samplingNumberColumn)
    # Test sequence number validity
    sequenceCorrect = functions.check_sequence_numbers(table, sampleMeasProgColumn,
                                                       sampleCIDColumn, samplingNumberColumn, locationNumberColumn)
    # Prepare message for user
    msg = ""
    if invalidColumns:
        listOfColumnNames = '\n'.join(column_config[k]['name']for k in invalidColumns)
        msg += "The following columns have invalid values:\n" + listOfColumnNames
        dataValid = False

    if incompleteColumns:
        listOfColumnNames = '\n'.join(column_config[k]['name']for k in incompleteColumns)
        if msg != "":
            msg += "\n\n"
        msg += "The following required columns have one or more empty values:\n" + listOfColumnNames
        dataValid = False

    if matrixConsistent is False:
        if msg != "":
            msg += "\n\n"
        msg += "Matrix errors detected:\n" \
               "More than one matrix has been defined for a single sampling event.\n" \
               "Please ensure that only a single matrix is used for all samples in a " \
               "sampling event (for primary and replicates) before exporting."
        dataValid = False

    if sequenceCorrect is False:
        if msg != "":
            msg += "\n\n"
        msg += "Sequence number errors detected:\nOne or more problems have been " \
               "detected with the provided sequence numbers. Please ensure that:\n" \
               "- All samples in a single sampling event use distinct sequence numbers;\n" \
               "- The first sample in all sampling events is 1;\n" \
               "- All sequence numbers in a single sampling event increment sequentially." \
               "\nA sampling event consists of all samples collected at the same station " \
               "on the same date."
        dataValid = False

    return dataValid, msg


class filteredComboBox(QtGui.QComboBox):
    # create returnPressed signal
    returnPressed = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(filteredComboBox, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)
        # add a filter model to filter matching items
        self.pFilterModel = QtGui.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())
        # add a completer, which uses the filter model
        self.completer = QtGui.QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        # connect signals
        def filter(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited[unicode].connect(filter)
        self.completer.activated.connect(self.on_completer_activated)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)
            self.returnPressed.emit()


class listColumnItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self):
        super(listColumnItemDelegate, self).__init__()

    def createEditor(self, parent, option, index):
        combo = filteredComboBox(parent)
        try:
            items = ['']
            items.extend(column_config[index.column()]['list_items'])
            combo.addItems(items)
            editor = combo
        except KeyError:
            editor = super(listColumnItemDelegate, self).createEditor(parent, option, index)

        samplingNumberCol = functions.get_column_number("sampling_number")
        if index.column() == samplingNumberCol:
            editor.setReadOnly(True)

        editor.returnPressed.connect(self.commitAndCloseEditor)

        return editor

    def commitAndCloseEditor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QtGui.QAbstractItemDelegate.NoHint)


# -----------------------------------------------------------------------------
def main():
    """
    Run the Field Data Formatter app
    """
    app = QtGui.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
