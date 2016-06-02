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

import sys
from PyQt4 import QtGui, QtCore
import fdfGui
import functions
import globals


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
                self.tableWidgetData.setItem(rowPosition, j, QtGui.QTableWidgetItem(str(lists[i][j])))
        #self._setTableDropDowns()
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
        #self._validateBeforeExport()
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

    def _setTableDropDowns(self):
        table = self.tableWidgetData
        for row in range(0, table.rowCount()):
            for col in globals.COL_NUM.itervalues():
                table.openPersistentEditor(table.item(row, col))

    def _autoUpdateCols(self, item):
        table = self.tableWidgetData
        table.blockSignals(True)
        row = item.row()
        col = item.column()
        if col in [2, 3]:  # Sampling datetime
            date = str(table.item(row, 2).text())
            time = str(table.item(row, 3).text())
            sampleDateTime = functions.parse_datetime_from_string(date, time)
            table.setItem(row, 2, QtGui.QTableWidgetItem(sampleDateTime.strftime(globals.DATE_DISPLAY)))
            table.setItem(row, 3, QtGui.QTableWidgetItem(sampleDateTime.strftime(globals.TIME_DISPLAY)))
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
        paramName = ""
        for parameter, column in globals.COL_NUM.iteritems():
            if column == col:
                try:
                    lowerLimit = globals.LIMITS[parameter.lower()][0]
                    upperLimit = globals.LIMITS[parameter.lower()][1]
                    paramName = parameter
                except KeyError:
                    return None
        validator = QtGui.QDoubleValidator(lowerLimit, upperLimit, 2)

        # if item.column() == globals.COL_NUM['PH']:
        #     validator = QtGui.QDoubleValidator(0, 14, 2)
        # if item.column() ==

        state = validator.validate(item.text(), 0)[0]
        print state
        if state != QtGui.QValidator.Acceptable:
            item.setBackgroundColor(QtCore.Qt.red)
            txt = "%s value out of range.\n Acceptable range is between %s and %s" % (paramName, lowerLimit, upperLimit)
            msg = QtGui.QMessageBox()
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText(txt)
            msg.setWindowTitle("Error!")
            msg.exec_()
        else:
            item.setBackgroundColor(QtCore.Qt.white)
        self.tableWidgetData.blockSignals(False)

    # def _validateBeforeExport(self):
    #     rows = self.tableWidgetData.rowCount()
    #     cols = self.tableWidgetData.columnCount()
    #     for i in range(0, rows):
    #         for j in range(0, cols):
    #             item = self.tableWidgetData.item(i, j)
    #             for parameter, column in globals.COL_NUM.iteritems():
    #                 if column == j:
    #                     try:
    #                         lowerLimit = globals.LIMITS[parameter.lower()][0]
    #                         upperLimit = globals.LIMITS[parameter.lower()][1]
    #                     except KeyError:
    #                         return None
    #             validator = QtGui.QDoubleValidator(lowerLimit, upperLimit, 2)
    #             state = validator.validate(item.text(), 0)[0]
    #             if state != QtGui.QValidator.Acceptable:
    #                 msg = QtGui.QMessageBox()
    #                 msg.setIcon(QtGui.QMessageBox.Warning)
    #                 msg.setText("Errors detected. Please correct cells in red before proceeding.")
    #                 msg.setWindowTitle("Error!")
    #                 msg.exec_()
    #                 return None


class validatedItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self):
        super(validatedItemDelegate, self).__init__()

    def createEditor(self, parent, option, index):
        combo = QtGui.QComboBox(parent)
        if index.column() == globals.COL_NUM['MP_NUMBER']:
            items = globals.MP_NUMBERS
        elif index.column() == globals.COL_NUM['SAMPLE_TYPE']:
            items = globals.SAMPLE_TYPES
        elif index.column() == globals.COL_NUM['SAMPLE_MATRIX']:
            items = globals.MATRIX_TYPES
        elif index.column() == globals.COL_NUM['SAMPLING_OFFICER']:
            items = globals.FIELD_STAFF
        elif index.column() == globals.COL_NUM['SAMPLE_COLLECTED']:
            items = globals.BOOLEAN
        elif index.column() == globals.COL_NUM['SAMPLING_INSTRUMENT']:
            items = globals.INSTRUMENTS
        else:
            return super(validatedItemDelegate, self).createEditor(parent, option, index)
        combo.addItems(items)
        return combo



    # def createEditor(self, parent, option, index):
    #     self.editor = QtGui.QComboBox(parent)
    #     self.editor.addItems(globals.SAMPLE_TYPES)
    #     return self.editor
        # if not index.isValid():
        #     return
        # row = index.row()
        # col = index.column()
        # if col == 8:
        #     cb = QtGui.QComboBox()
        #     cb.addItems(globals.SAMPLE_TYPES)
        #     return cb
        # if col == any([1, 2]):
        #     widget.setItem(row, 4, QtGui.QTableWidgetItem(functions.get_sampling_number(
        #         station_number=str(widget.item(row, 1).text()),
        #         date=str(widget.item(row, 2).text()),
        #         sample_type=str(widget.item(row, 8).text())
        #     )))
        #return super(validatedItemDelegate, self).createEditor(parent, option, index)

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
