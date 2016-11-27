from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot
import functions
from functions import DatetimeError, ValidityError
from configuration import app_config, column_config


##############################################################################
# Style delegates
##############################################################################
class tableDelegate(QtGui.QStyledItemDelegate):
    def __init__(self):
        super(tableDelegate, self).__init__()

    def createEditor(self, parent, option, index):

        if 'list_items' in column_config[index.column()]:
            editor = QtGui.QComboBox()
            editor.addItems(column_config[index.column()]['list_items'])
            return editor
        else:
            return super(tableDelegate, self).createEditor(parent, option, index)

        # combo = FilteredComboBox(parent)
        # try:
        #     items = ['']
        #     items.extend(column_config[index.column()]['list_items'])
        #     combo.addItems(items)
        #     editor = combo
        # except KeyError:
        #     editor = super(ListColumnItemDelegate, self).createEditor(parent, option, index)
        #     samplingNumberCol = functions.get_column_number("sampling_number")
        #     if index.column() == samplingNumberCol:
        #         editor.setReadOnly(True)
        #
        # editor.returnPressed.connect(self.commitAndCloseEditor)

        # TODO: setModel to set model to proxyFilterModel
        # TODO: setValidator
        # return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index)
        # TODO: set the editor data here

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def setModelData(self, editor, model, index):
        if type(editor) is QtGui.QComboBox:
            valueFunc = editor.currentText
        else:
            valueFunc = editor.text
        value = valueFunc()
        model.setData(index, value)

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
        @pyqtSlot()
        def filter(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited[unicode].connect(filter)
        self.completer.activated.connect(self.onCompleterActivated)

    # On selection of an item from the completer, select the corresponding item from combobox
    def onCompleterActivated(self, text):
        if text:
            self.returnPressed.emit()
