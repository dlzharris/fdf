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
# TODO: Manager-cofigs to separate yaml file;
# TODO: other configs to yaml;
# TODO: Dropdown only one return push to select and exit
# TODO: Update help documentation html
# TODO: Tidy GUI elements
# TODO: Code clean and document

import sys
import os
from PyQt4 import QtGui, QtCore
import fdfGui
import functions
from functions import DatetimeError, ValidityError
import globals
import yaml

# Load config files
column_config = yaml.load(open('column_config.yaml').read())

###############################################################################
# Main app constructor and initialisation
###############################################################################
class MainApp(fdfGui.Ui_MainWindow, QtGui.QMainWindow):
    """
    Constructor for the main application
    """
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.filePickerBtn.clicked.connect(self._filePicker)
        self.addFileBtn.clicked.connect(self._addFile)
        self.pushButtonDeleteLines.clicked.connect(self._delRows)
        self.pushButtonAddLines.clicked.connect(self._insertRows)
        self.pushButtonResetData.clicked.connect(self._resetData)
        self.pushButtonExportData.clicked.connect(self._exportData)
        # Add items to the instrument picker
        _instruments = ['']
        _instruments.extend(column_config[10]['list_items'])
        self.instrumentComboBox.addItems(_instruments)
        # Set up the table
        table = self.tableWidgetData
        table.setItemDelegate(validatedItemDelegate())
        table.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed | QtGui.QAbstractItemView.DoubleClicked)
        table.itemChanged.connect(self._autoUpdateCols)
        table.itemChanged.connect(self._validateInput)
        # Set up the help documentation
        self.helpBrowser = QtGui.QTextBrowser()
        self.helpBrowser.setSource(QtCore.QUrl('help.html'))
        self.helpBrowser.setWindowTitle("FDF Utility Help Documentation")
        self.helpBrowser.setMinimumSize(500, 500)
        self.pushButtonHelp.clicked.connect(self._showHelp)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self._copy()
        elif event.matches(QtGui.QKeySequence.Paste):
            self._paste()
        else:
            QtGui.QMainWindow.keyPressEvent(self, event)

    def _showHelp(self):
        self.helpBrowser.show()

    def _filePicker(self):
        # Show file picker dialog and show name in text box
        self.fileLineEdit.setText(QtGui.QFileDialog.getOpenFileName())

    def _addFile(self):
        try:
            # Validate file type
            _dicts = functions.load_instrument_file(self.fileLineEdit.text(), str(self.instrumentComboBox.currentText()))
            self._addData(functions.lord2lorl(_dicts, globals.COL_ORDER))
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
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                try:
                    validator = DoubleFixupValidator(item.column())
                    state, displayValue, returnInt = validator.validate(item.text(), 0)
                    if state == QtGui.QValidator.Invalid:
                        item.setBackgroundColor(QtCore.Qt.red)
                        errorsFound = True
                except KeyError:
                    pass
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
        rows = self.tableWidgetData.selectionModel().selectedRows()
        rowCount = len(rows)
        try:
            rowPosition = rows[0].row()
        except IndexError:
            rowPosition = self.tableWidgetData.rowCount()
            rowCount = 1
        for i in range(0, rowCount):
            self.tableWidgetData.insertRow(rowPosition)
        self._setTableDropDowns()

    def _delRows(self):
        rows = self.tableWidgetData.selectionModel().selectedRows()
        rows.reverse()
        for r in rows:
            self.tableWidgetData.removeRow(r.row())

    def _resetData(self):
        self.tableWidgetData.setRowCount(0)

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
        tableData = functions.lorl2lord(tableData, globals.COL_ORDER)
        # Reformat the data in parameter-oriented format
        data_reformatted = functions.prepare_dictionary(tableData)
        # Write the data to csv
        msg = QtGui.QMessageBox()
        try:
            # Write to sample oriented file for QA
            if self.chkBoxSampleOriented.isChecked():
                fn = os.path.splitext(str(fileName))[0] + '_sampleOriented' + '.csv'
                functions.write_to_csv(tableData, fn, globals.COL_ORDER)
            # Write to parameter oriented file for import to KiWQM
            if functions.write_to_csv(data_reformatted, fileName, globals.FIELDNAMES):
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
        selection = self.tableWidgetData.selectionModel()
        indexes = selection.selectedIndexes()
        # Get the location of the top left cell in selection
        pasteStartRow = min(r.row() for r in indexes)
        pasteStartCol = min(c.column() for c in indexes)
        if len(indexes) < 1:
            # Nothing selected
            return
        # Parse the clipboard
        copyDataRows = QtGui.QApplication.clipboard().text().split('\n')
        # Paste data in rows, starting from top and moving left to right
        for i in range(0, len(copyDataRows)):
            copyDataCols = copyDataRows[i].split('\t')
            for j in range(0, len(copyDataCols)):
                self.tableWidgetData.setItem(pasteStartRow + i,
                                             pasteStartCol + j,
                                             QtGui.QTableWidgetItem(copyDataCols[j]))

    def _autoUpdateCols(self, item):
        table = self.tableWidgetData
        table.blockSignals(True)
        row = item.row()
        col = item.column()
        if col in [2, 3]:  # Sampling datetime
            date = str(table.item(row, 2).text())
            time = str(table.item(row, 3).text())
            try:
                sampleDateTime = functions.parse_datetime_from_string(date, time)
                table.setItem(row, 2, QtGui.QTableWidgetItem(sampleDateTime.strftime(globals.DATE_DISPLAY)))
                table.setItem(row, 3, QtGui.QTableWidgetItem(sampleDateTime.strftime(globals.TIME_DISPLAY)))
            except DatetimeError:
                table.setItem(row, col, QtGui.QTableWidgetItem(""))
                table.item(row, col).setBackgroundColor(QtCore.Qt.red)
                if col == 2:
                    param = "date"
                else:
                    param = "time"
                txt = "%s value not valid.\n Please enter a valid %s" % (param.title(), param)
                windowTitleTxt = "Datetime error!"
                msg = QtGui.QMessageBox()
                msg.setIcon(QtGui.QMessageBox.Warning)
                msg.setText(txt)
                msg.setWindowTitle(windowTitleTxt)
                msg.exec_()
                table.blockSignals(False)
                return

        if col in [1, 2]:  # Sampling number
            stationNumber = str(table.item(row, 1).text())
            date = str(table.item(row, 2).text())
            sampleType = str(table.item(row, 8).text())
            samplingNumber = functions.get_sampling_number(
                station_number=stationNumber,
                date=date,
                sample_type=sampleType)
            table.setItem(row, 4, QtGui.QTableWidgetItem(samplingNumber))
            table.item(row, 4).setTextAlignment(QtCore.Qt.AlignCenter)
        table.blockSignals(False)

    def _validateInput(self, item):
        self.tableWidgetData.blockSignals(True)
        col = item.column()
        try:
            validator = ListValidator(col)
        except KeyError:
            try:
                validator = DoubleFixupValidator(col)
            except KeyError:
                self.tableWidgetData.blockSignals(False)
                return
        state, displayValue, returnInt = validator.validate(item.text(), 0)
        if state != QtGui.QValidator.Acceptable:
            paramName = column_config[col]['name']
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
            else:  # returnInt == 2 List error
                txt = "%s value is not a valid value from the drop down list." \
                      "Please select a valid valud from the list." % paramName
                windowTitleTxt = "Invalid selection error!"
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(txt)
            msg.setWindowTitle(windowTitleTxt)
            msg.exec_()
        else:
            item.setText(displayValue)
            item.setBackgroundColor(QtCore.Qt.white)

        self.tableWidgetData.blockSignals(False)


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
    sampleMatrixColumn = [k for k, v in column_config.iteritems() if v['name'] == 'sample_matrix'][0]
    samplingNumberColumn = [k for k, v in column_config.iteritems() if v['name'] == 'sampling_number'][0]
    sampleCIDColumn = [k for k, v in column_config.iteritems() if v['name'] == 'sample_cid'][0]
    locationNumberColumn = [k for k, v in column_config.iteritems() if v['name'] == 'location_id'][0]
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
    matrixConsistent = functions.check_matrix_consistency(table, sampleMatrixColumn, samplingNumberColumn)
    # Test sequence number validity
    sequenceCorrect = functions.check_sequence_numbers(table, sampleCIDColumn, samplingNumberColumn, locationNumberColumn)
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


class validatedItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self):
        super(validatedItemDelegate, self).__init__()

    def createEditor(self, parent, option, index):
        combo = filteredComboBox(parent)
        try:
            items = ['']
            items.extend(column_config[index.column()]['list_items'])
            combo.addItems(items)
            return combo
        except KeyError:
            return super(validatedItemDelegate, self).createEditor(parent, option, index)


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
