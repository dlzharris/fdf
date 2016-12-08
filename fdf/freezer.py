#!python3
#http://python.su/forum/viewtopic.php?id=7346
import sys
from PyQt4 import QtGui, QtCore


class MyWindow(QtGui.QWidget):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)

        # create table
        table = FreezeTableWidget(self)

        # layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(table)
        self.setLayout(layout)

# TODO: Align frozen column and thawed column on add data
# TODO: Let frozen column accept focus (or editor to accept focus) when editing - this must happen through the viewport
class FreezeTableWidget(QtGui.QTableView):
    def __init__(self, model, parent=None):
        QtGui.QTableView.__init__(self, parent)

        # Assign a data model for TableView
        self.setModel(model)

        # Set the number of frozen columns
        self.frozenColumns = 2

        # *** WIDGET recorded COLUMN ***
        # (To be located on top of the ground)
        self.frozenTableView = QtGui.QTableView(self)
        # Set the model for the widget, fixed column
        self.frozenTableView.setModel(model)
        # Hide row headers
        self.frozenTableView.verticalHeader().hide()
        # Widget does not accept focus
        self.frozenTableView.setFocusPolicy(QtCore.Qt.NoFocus)
        # The user can not resize columns
        self.frozenTableView.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        # Puts more widgets to the foreground
        self.viewport().stackUnder(self.frozenTableView)
        # Disable the display of the widget borders
        #self.frozenTableView.setStyleSheet('''border: none; background-color: #8EDE21;
         #                              selection-background-color: #999''')
        # Selection mode as in the main widget
        self.frozenTableView.setSelectionModel(self.selectionModel())

        # Set the width of columns
        for column in range(self.frozenColumns, model.columnCount()):
            self.frozenTableView.setColumnHidden(column, True)
            self.frozenTableView.setColumnWidth(column, self.columnWidth(column))

        # Remove the scroll bar
        self.frozenTableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.frozenTableView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Set the size of him like the main
        self.updateFrozenTableGeometry()

        # Set the scroll mode to keep in sync
        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.frozenTableView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        # TODO: may need to comment this - see how it goes
        # Log in to edit mode - even with one click
        #self.setEditTriggers(QtGui.QAbstractItemView.SelectedClicked)
        # Set the font
        #self.setStyleSheet('font: 10pt "Courier New"')
        # Set the properties of the column headings
        #hh = self.horizontalHeader()
        # Text alignment centered
        #hh.setDefaultAlignment(QtCore.Qt.AlignCenter)
        # Include stretching the last column
        #hh.setStretchLastSection(True)



        # Turn the alternating illumination lines
        #self.setAlternatingRowColors(True)

        # TODO: When adding data, vertical header (line numbers) become visible and push bottom table out
        # TODO: Therefore, need to ensure vertical headers are in sync
        # Set properties header lines
        #vh = self.verticalHeader()
        #vh.setDefaultSectionSize(25)  # Row heights
        #vh.setDefaultAlignment(QtCore.Qt.AlignCenter)  # Text alignment centered
        #vh.setVisible(True)
        # Height of rows - as in the main widget
        #self.frozenTableView.verticalHeader().setDefaultSectionSize(vh.defaultSectionSize())

        # Show our optional widget
        self.frozenTableView.show()

        # Create a connection
        # connect the headers and scrollbars of both tableviews together
        self.horizontalHeader().sectionResized.connect(self.updateSectionWidth)
        self.verticalHeader().sectionResized.connect(self.updateSectionHeight)
        self.frozenTableView.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self.frozenTableView.verticalScrollBar().setValue)
        model.verticalHeaderChanged.connect(self.updateFrozenTableGeometry)

    def updateSectionWidth(self, logicalIndex, oldSize, newSize):
        if logicalIndex < self.frozenColumns:
            self.frozenTableView.setColumnWidth(logicalIndex, newSize)
            self.updateFrozenTableGeometry()

    def updateSectionHeight(self, logicalIndex, oldSize, newSize):
        self.frozenTableView.setRowHeight(logicalIndex, newSize)

    def resizeEvent(self, event):
        QtGui.QTableView.resizeEvent(self, event)
        self.updateFrozenTableGeometry()

    def scrollTo(self, index, hint):
        if index.column() > 1:
            QtGui.QTableView.scrollTo(self, index, hint)

    def updateFrozenTableGeometry(self):
        self.frozenTableView.setGeometry(
            self.verticalHeader().width(),
            0, sum([self.frozenTableView.columnWidth(i) for i in range(self.frozenColumns)]),
            self.viewport().height() + self.horizontalHeader().height()
        )

    # MoveCursor override function for correct left to scroll the keyboard
    def moveCursor(self, cursorAction, modifiers):
        current = QtGui.QTableView.moveCursor(self, cursorAction, modifiers)

        if cursorAction == self.MoveLeft and current.column() > (self.frozenColumns - 1) and \
                        self.visualRect(current).topLeft().x() < sum([self.frozenTableView.columnWidth(i)
                                                                      for i in range(self.frozenColumns)]):
            newValue = self.horizontalScrollBar().value() \
                       + self.visualRect(current).topLeft().x() \
                       - sum([self.frozenTableView.columnWidth(i) for i in range(self.frozenColumns)])

            self.horizontalScrollBar().setValue(newValue)

        return current
