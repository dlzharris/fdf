from PyQt4 import QtGui, QtCore


class FreezeTableWidget(QtGui.QTableView):
    def __init__(self, model, parent=None):
        QtGui.QTableView.__init__(self, parent)
        # Set the model
        self.model = model
        # Assign a data model for TableView
        self.setModel(self.model)
        # Set the number of frozen columns
        self.frozenColumns = 3
        # *** WIDGET recorded COLUMN ***
        # (To be located on top of the ground)
        self.frozenTableView = QtGui.QTableView(self)
        # Set the model for the widget, fixed column
        self.frozenTableView.setModel(self.model)
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
        self.setHiddenColumns(self.frozenColumns)

        # Remove the scroll bar
        self.frozenTableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.frozenTableView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Set the size of him like the main
        self.updateFrozenTableGeometry()

        # Set the scroll mode to keep in sync
        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.frozenTableView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        # Turn the alternating illumination lines
        # self.setAlternatingRowColors(True)

        # Show our optional widget
        self.frozenTableView.show()

        # Create a connection
        # connect the headers and scrollbars of both tableviews together
        self.horizontalHeader().sectionResized.connect(self.updateSectionWidth)
        self.verticalHeader().sectionResized.connect(self.updateSectionHeight)
        self.frozenTableView.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self.frozenTableView.verticalScrollBar().setValue)
        self.model.verticalHeaderChanged.connect(self.updateFrozenTableGeometry)

    def setHiddenColumns(self, frozenColumns):
        for column in range(self.frozenColumns, self.model.columnCount()):
            self.frozenTableView.setColumnHidden(column, True)
            self.frozenTableView.setColumnWidth(column, self.columnWidth(column))
        self.updateFrozenTableGeometry()

    def updateFrozenColumns(self, frozenColumns):
        self.frozenColumns = frozenColumns
        self.setHiddenColumns(frozenColumns)
    
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

    def selectionChanged(self, selected, deselected):
        columns = set(index.column() for index in selected.indexes())

        if columns and all(i < self.frozenColumns for i in columns):
            self.frozenTableView.setFocus()
        else:
            self.setFocus()

