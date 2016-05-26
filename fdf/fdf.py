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

    def _filePicker(self):
        # Show file picker dialog and show name in text box
        self.fileLineEdit.setText(QtGui.QFileDialog.getOpenFileName())

    def _addFile(self):
        # Validate file type
        _dicts = functions.load_instrument_file(self.fileLineEdit.text(), "Hydrolab DS5")
        self._addRows(functions.lord2lorl(_dicts, globals.COL_ORDER))
        self.listWidgetCurrentFiles.addItem(QtGui.QListWidgetItem(self.fileLineEdit.text()))
        # Add file name to listbox

    def _addRows(self, lists):
        for i in range(0, len(lists)):
            rowPosition = self.tableWidgetData.rowCount()
            self.tableWidgetData.insertRow(rowPosition)
            for j in range(0, len(lists[i])):
                self.tableWidgetData.setItem(rowPosition, j, QtGui.QTableWidgetItem(str(lists[i][j])))

    def _delRows(self):
        rows = self.tableWidgetData.selectionModel().selectedRows()
        rows.reverse()
        for r in rows:
            self.tableWidgetData.removeRow(r.row())

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
