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


class FreezeTableWidget(QtGui.QTableView):
    def __init__(self, model, parent=None):
        QtGui.QTableView.__init__(self, parent)

        # The minimum size of the window
        #TODO: set this outside
        #self.setMinimumSize(800, 600)

        # Assign a data model for TableView
        self.setModel(model)

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
        # Disable the display of the widget borders
        #self.frozenTableView.setStyleSheet('''border: none; background-color: #8EDE21;
         #                              selection-background-color: #999''')
        # Selection mode as in the main widget
        self.frozenTableView.setSelectionModel(self.selectionModel())
        # Remove the scroll bar
        self.frozenTableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.frozenTableView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Puts more widgets to the foreground
        self.viewport().stackUnder(self.frozenTableView)

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

        # Set the width of columns
        thawed = 2
        for column in range(thawed, model.columnCount()):
            self.frozenTableView.setColumnHidden(column, True)

        # Turn the alternating illumination lines
        #self.setAlternatingRowColors(True)

        # Show our optional widget
        self.frozenTableView.show()
        # Set the size of him like the main
        self.updateFrozenTableGeometry()

        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.frozenTableView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        # Create a connection
        # connect the headers and scrollbars of both tableviews together
        self.horizontalHeader().sectionResized.connect(self.updateSectionWidth)
        self.verticalHeader().sectionResized.connect(self.updateSectionHeight)
        self.frozenTableView.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self.frozenTableView.verticalScrollBar().setValue)

    def updateSectionWidth(self, logicalIndex, oldSize, newSize):
        if logicalIndex == 0 or logicalIndex == 1:
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
        if self.verticalHeader().isVisible():
            self.frozenTableView.setGeometry(self.verticalHeader().width() + self.frameWidth(),
                         self.frameWidth(), self.columnWidth(0) + self.columnWidth(1),
                         self.viewport().height() + self.horizontalHeader().height())
        else:
            self.frozenTableView.setGeometry(self.frameWidth(),
                         self.frameWidth(), self.columnWidth(0) + self.columnWidth(1),
                         self.viewport().height() + self.horizontalHeader().height())

    # MoveCursor override function for correct left to scroll the keyboard
    def moveCursor(self, cursorAction, modifiers):
        current = QtGui.QTableView.moveCursor(self, cursorAction, modifiers)
        if cursorAction == self.MoveLeft and current.column() > 1 and self.visualRect(current).topLeft().x() < (self.frozenTableView.columnWidth(0) + self.frozenTableView.columnWidth(1)):
            newValue = self.horizontalScrollBar().value() + self.visualRect(current).topLeft().x() - (self.frozenTableView.columnWidth(0) + self.frozenTableView.columnWidth(1))
            self.horizontalScrollBar().setValue(newValue)
        return current

    def setItemDelegate(self, delegate):
        super(FreezeTableWidget, self).setItemDelegate(delegate)
        self.frozenTableView.setItemDelegate(delegate)