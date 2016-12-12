from PyQt4 import QtGui, QtCore
import functions
import settings
from settings import column_config

##############################################################################
# Style delegates
##############################################################################
class tableDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, tableFrozen=False):
        super(tableDelegate, self).__init__()
        self.tableFrozen = tableFrozen

    def createEditor(self, parent, option, index):
        items = [""]

        if 'list_items' in column_config[index.column()] and index.column() < settings.FROZEN_COLUMNS:
            if self.tableFrozen:
                editor = FilteredComboBox(parent)
                items.extend(column_config[index.column()]['list_items'])
                editor.addItems(items)
                validator = ListValidator(index.column())
                editor.setValidator(validator)
                editor.activated.connect(self.commitAndCloseEditor)
                return editor
            else:
                return None

        if 'list_items' in column_config[index.column()] and index.column() >= settings.FROZEN_COLUMNS:
            editor = FilteredComboBox(parent)
            items.extend(column_config[index.column()]['list_items'])
            editor.addItems(items)
            validator = ListValidator(index.column())
            editor.setValidator(validator)
            editor.activated.connect(self.commitAndCloseEditor)
            return editor

        elif 'date' in column_config[index.column()]['name']:
            editor = QtGui.QDateTimeEdit(parent)
            editor.setDateRange(QtCore.QDate(2014, 1, 1), QtCore.QDate.currentDate())
            editor.setDisplayFormat("yyyy-MM-dd")
            return editor

        elif 'time' in column_config[index.column()]['name']:
            editor = QtGui.QDateTimeEdit(parent)
            editor.setDisplayFormat("HH:mm:ss")
            return editor

        elif 'lower_limit' in column_config[index.column()]:
            editor = QtGui.QLineEdit(parent)
            validator = DoubleFixupValidator(index.column(), editor)
            validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
            editor.setValidator(validator)
            return editor

        elif index.column() < settings.FROZEN_COLUMNS:
            if self.tableFrozen:
                return super(tableDelegate, self).createEditor(parent, option, index)
            else:
                return None

        else:
            return super(tableDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        value = index.model().data(index)

        if type(editor) is FilteredComboBox:
            editor.setCurrentIndex(editor.findText(value))
        elif index.column() == functions.get_column_number('date'):
            editor.setDate(QtCore.QDate.fromString(value, QtCore.Qt.ISODate))
        elif index.column() == functions.get_column_number('time'):
            editor.setTime(QtCore.QTime.fromString(value, QtCore.Qt.ISODate))
        else:
            editor.setText(QtCore.QString(value))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def setModelData(self, editor, model, index):
        if type(editor) is FilteredComboBox:
            value = editor.currentText()
        elif index.column() == functions.get_column_number('date'):
            value = editor.date()
        elif index.column() == functions.get_column_number('time'):
            value = editor.time()
        elif 'lower_limit' in column_config[index.column()]:
            value = editor.text()
        else:
            value = editor.text()

        model.setData(index, value)

    def commitAndCloseEditor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QtGui.QAbstractItemDelegate.EditNextItem)


##############################################################################
# Widgets
##############################################################################
class FilteredComboBox(QtGui.QComboBox):
    """
    Creates a combo box that filters the available options based on user
    input, in a similar way to jQuery.
    """

    def __init__(self, parent=None):
        super(FilteredComboBox, self).__init__(parent)

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
        self.lineEdit().textEdited[unicode].connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.onCompleterActivated)

    # on selection of an item from the completer, select the corresponding item from combobox
    def onCompleterActivated(self, text):
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)


##############################################################################
# Validator classes
##############################################################################
class DoubleFixupValidator(QtGui.QDoubleValidator):
    def __init__(self, column, parent):
        self.column = column
        self.bottom = column_config[self.column]['lower_limit']
        self.top = column_config[self.column]['upper_limit']
        self.decimals = column_config[self.column]['precision']
        super(DoubleFixupValidator, self).__init__(self.bottom, self.top, self.decimals, parent)

    def validate(self, value, pos):

        state, pos = QtGui.QDoubleValidator.validate(self, value, pos)

        if value.isEmpty() or value == '.' or value == '-':
            return QtGui.QValidator.Intermediate, pos

        if state != QtGui.QValidator.Acceptable:
            self.fixup(value)
            if value.toFloat() > self.top or value.toFloat < self.bottom:
                return QtGui.QValidator.Invalid, pos

        return QtGui.QDoubleValidator.validate(self, value, pos)

    def fixup(self, value):
        """Rounds value to precision specified in column_config."""
        if value:
            rounded = round(float(value), self.decimals)
            value.setNum(rounded)

        return None


class ListValidator(QtGui.QRegExpValidator):
    def __init__(self, column):
        self.column = column
        self.list = column_config[self.column]['list_items']
        self.pattern = '|'.join(self.list)

        super(ListValidator, self).__init__(QtCore.QRegExp(self.pattern))

    def validate(self, value, pos):
        state, pos = QtGui.QRegExpValidator.validate(self, value, pos)

        if state == QtGui.QValidator.Invalid:
            self.fixup(value)
            pos = value.length()
            state, pos = QtGui.QRegExpValidator.validate(self, value, pos)

        return state, pos

    def fixup(self, value):
        if self.column == functions.get_column_number('mp_number') and value.toInt()[1]:
            value.insert(0, 'MP')

        upper = value.toUpper()
        value.clear()
        value.append(upper)

        return None
