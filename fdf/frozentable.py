"""
Module: frozentable.py
Class definition for QTableView with frozen columns at left-hand side.

Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/12/2016

External dependencies: PyQt4
FreezeTableWidget: TableView class with frozen colunmns.
Adapted from http://blindvic.blogspot.com.au/2010/12/frozen-column-example-pyqt4-python3.html
"""

from PyQt4 import QtGui, QtCore

__author__ = 'Daniel Harris'
__date__ = '12 December 2016'
__email__ = 'daniel.harris@dpi.nsw.gov.au'
__status__ = 'Production'
__version__ = '1.0.0'


class FreezeTableWidget(QtGui.QTableView):
    def __init__(self, model, parent=None):
        QtGui.QTableView.__init__(self, parent)
        # Set the model
        self.model = model
        # Assign a data model for TableView
        self.setModel(self.model)
        # Set the number of frozen columns
        self.frozenColumns = 3
        # Create a second QTableView with original table as parent
        self.frozenTableView = QtGui.QTableView(self)
        # Set the model for the frozen table
        self.frozenTableView.setModel(self.model)
        # Hide row headers
        self.frozenTableView.verticalHeader().hide()
        # Allow focus on frozen table
        self.frozenTableView.setFocusPolicy(QtCore.Qt.StrongFocus)
        # The user can not resize columns
        self.frozenTableView.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        # Puts more widgets to the foreground
        self.viewport().stackUnder(self.frozenTableView)
        # Disable the display of the widget borders
        self.frozenTableView.setStyleSheet('''border: none;''')
        # Use the same selection model as the main table
        self.frozenTableView.setSelectionModel(self.selectionModel())
        # Hide the non-frozen columns
        self.setHiddenColumns(self.frozenColumns)
        # Remove the scroll bar
        self.frozenTableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.frozenTableView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # Set the sorting
        self.frozenTableView.setSortingEnabled(True)
        # Update the size and location of the frozen table with respect to the main table
        self.updateFrozenTableGeometry()
        # Set the scroll mode to keep in sync
        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.frozenTableView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        # Show our frozen table
        self.frozenTableView.show()
        # Create connections - connect the headers and scrollbars of both tableviews together
        self.horizontalHeader().sectionResized.connect(self.updateSectionWidth)
        self.verticalHeader().sectionResized.connect(self.updateSectionHeight)
        self.frozenTableView.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self.frozenTableView.verticalScrollBar().setValue)
        self.model.verticalHeaderChanged.connect(self.updateFrozenTableGeometry)

    ##########################################################################
    # Reimplemented methods
    ##########################################################################
    def moveCursor(self, cursorAction, modifiers):
        """Override function for correct scrolling using the keyboard.
        Prevents main table disappearing behind frozen table."""
        current = QtGui.QTableView.moveCursor(self, cursorAction, modifiers)

        if cursorAction == self.MoveLeft and current.column() > (self.frozenColumns - 1) and \
                        self.visualRect(current).topLeft().x() < sum([self.frozenTableView.columnWidth(i)
                                                                      for i in range(self.frozenColumns)]):
            newValue = self.horizontalScrollBar().value() \
                       + self.visualRect(current).topLeft().x() \
                       - sum([self.frozenTableView.columnWidth(i) for i in range(self.frozenColumns)])

            self.horizontalScrollBar().setValue(newValue)

        return current

    def resizeEvent(self, event):
        QtGui.QTableView.resizeEvent(self, event)
        self.updateFrozenTableGeometry()

    def scrollTo(self, index, hint):
        if index.column() > 1:
            QtGui.QTableView.scrollTo(self, index, hint)

    def selectionChanged(self, selected, deselected):
        columns = set(index.column() for index in selected.indexes())

        if columns and all(i < self.frozenColumns for i in columns):
            self.frozenTableView.setFocus()
        else:
            self.setFocus()

    def updateSectionHeight(self, logicalIndex, oldSize, newSize):
        self.frozenTableView.setRowHeight(logicalIndex, newSize)

    def updateSectionWidth(self, logicalIndex, oldSize, newSize):
        if logicalIndex < self.frozenColumns:
            self.frozenTableView.setColumnWidth(logicalIndex, newSize)
            self.updateFrozenTableGeometry()

    ##########################################################################
    # Private methods
    ##########################################################################
    def setHiddenColumns(self, frozenColumns):
        """Hides all non-frozen columns in frozen table"""
        for column in range(self.frozenColumns, self.model.columnCount()):
            self.frozenTableView.setColumnHidden(column, True)
            self.frozenTableView.setColumnWidth(column, self.columnWidth(column))
        self.updateFrozenTableGeometry()

    def updateFrozenColumns(self, frozenColumns):
        """Updates the number of frozen columns"""
        for column in range(self.model.columnCount()):
            self.frozenTableView.setColumnHidden(column, False)
            self.frozenTableView.setColumnWidth(column, self.columnWidth(column))
        self.frozenColumns = frozenColumns
        self.setHiddenColumns(frozenColumns)

    def updateFrozenTableGeometry(self):
        """Sets the frozen table in the correct location and size"""
        self.frozenTableView.setGeometry(
            self.verticalHeader().width() + self.frameWidth(),
            self.frameWidth(), sum([self.frozenTableView.columnWidth(i) for i in range(self.frozenColumns)]),
            self.viewport().height() + self.horizontalHeader().height()
        )
