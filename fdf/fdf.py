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
# TODO: validate before export;
# TODO: cell styles;
# TODO: export to sample oriented as well
# TODO: Help documentation

import sys
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
        # Set up the table
        table = self.tableWidgetData
        table.setItemDelegate(validatedItemDelegate())
        table.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed | QtGui.QAbstractItemView.DoubleClicked)
        table.itemChanged.connect(self._autoUpdateCols)
        table.itemChanged.connect(self._validateInput)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self._copy()
        elif event.matches(QtGui.QKeySequence.Paste):
            self._paste()
        else:
            QtGui.QMainWindow.keyPressEvent(self, event)

    def _filePicker(self):
        # Show file picker dialog and show name in text box
        self.fileLineEdit.setText(QtGui.QFileDialog.getOpenFileName())

    def _addFile(self):
        # Validate file type
        _dicts = functions.load_instrument_file(self.fileLineEdit.text(), "Hydrolab DS5")
        self._addData(functions.lord2lorl(_dicts, globals.COL_ORDER))
        self.listWidgetCurrentFiles.addItem(QtGui.QListWidgetItem(self.fileLineEdit.text()))
        # Add file name to listbox

    def _addData(self, lists):
        self.tableWidgetData.blockSignals(True)
        for i in range(0, len(lists)):
            rowPosition = self.tableWidgetData.rowCount()
            self.tableWidgetData.insertRow(rowPosition)
            for j in range(0, len(lists[i])):
                value = str(lists[i][j])
                self.tableWidgetData.setItem(rowPosition, j, QtGui.QTableWidgetItem(value))
                item = self.tableWidgetData.item(i, j)
                try:
                    validator = DoubleFixupValidator(item)
                    state, displayValue, returnInt = validator.validate(item.text(), 0)
                    if state == QtGui.QValidator.Invalid:
                        item.setBackgroundColor(QtCore.Qt.red)
                except KeyError:
                    pass
        self.tableWidgetData.blockSignals(False)

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
        # TODO: Validate before export
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
        table.blockSignals(False)

    def _validateInput(self, item):
        self.tableWidgetData.blockSignals(True)
        col = item.column()
        try:
            validator = DoubleFixupValidator(col)
            state, displayValue, returnInt = validator.validate(item.text(), 0)
            if state != QtGui.QValidator.Acceptable:
                paramName = column_config[col]['name']
                item.setBackgroundColor(QtCore.Qt.red)
                if returnInt == 0:  # Zero-error
                    txt = "%s value has a value of zero (0).\n" \
                          "A value of zero generally indicates a sensor failure, or a non-measured parameter.\n" \
                          "Please review and adjust before continuing." % paramName
                    windowTitleTxt = "Data quality error!"
                else:  # returnInt == 1 Data range error
                    lowerLimit = column_config[col]['lower_limit']
                    upperLimit = column_config[col]['upper_limit']
                    txt = "%s value out of range.\n Acceptable range is between %s and %s" % (paramName, lowerLimit, upperLimit)
                    windowTitleTxt = "Value range error!"
                msg = QtGui.QMessageBox()
                msg.setIcon(QtGui.QMessageBox.Warning)
                msg.setText(txt)
                msg.setWindowTitle(windowTitleTxt)
                msg.exec_()
            else:
                item.setText(displayValue)
                item.setBackgroundColor(QtCore.Qt.white)
        except KeyError:
            self.tableWidgetData.blockSignals(False)
            return
        self.tableWidgetData.blockSignals(False)


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
    print table.item(0, 2).text()
    print table.item(0, 3).text()
    # Test for presence of data
    if rows <= 0:
        dataValid = False
        msg = "There is no data to export! Please add data and try again."
        return dataValid, msg
    # Test for red cells (previously validated)
    invalidColumns = []
    try:
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
    except AttributeError:
        print "i (column): %s" % i
        print "j (row): %s" % j
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


class validatedItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self):
        super(validatedItemDelegate, self).__init__()

    def createEditor(self, parent, option, index):
        combo = QtGui.QComboBox(parent)
        try:
            items = column_config[index.column()]['list_items']
            combo.addItems(items)
            cp = QtGui.QCompleter()
            cp.setCompletionMode(QtGui.QCompleter.PopupCompletion)
            combo.setCompleter(cp)
            #combo.completer().setCompletionMode(QtGui.QCompleter.PopupCompletion)
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
