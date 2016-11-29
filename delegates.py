from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot
import datetime
import functions
from functions import DatetimeError, ValidityError
from configuration import app_config, column_config
from dateutil.parser import parse


##############################################################################
# Style delegates
##############################################################################
class tableDelegate(QtGui.QStyledItemDelegate):
    def __init__(self):
        super(tableDelegate, self).__init__()

    def createEditor(self, parent, option, index):

        items = [""]

        if 'list_items' in column_config[index.column()]:
            editor = FilteredComboBox(parent)
            items.extend(column_config[index.column()]['list_items'])
            editor.addItems(items)
            return editor

        elif 'date' in column_config[index.column()]['name']:
            editor = QtGui.QDateTimeEdit(parent)
            #editor.setDateRange(QtCore.QDate(1970, 1, 1), QtCore.QDate.currentDate())
            editor.setDisplayFormat("dd/MM/yyyy")
            #editor.calendarPopup()
            return editor

        elif 'time' in column_config[index.column()]['name']:
            editor = QtGui.QDateTimeEdit(parent)
            editor.setDisplayFormat("hh:mm:ss")
            return editor

        else:
            return super(tableDelegate, self).createEditor(parent, option, index)

        # TODO: setValidator

    def setEditorData(self, editor, index):
        value = index.model().data(index)

        if type(editor) is FilteredComboBox:
            editor.setCurrentIndex(editor.findText(value))
        elif index.column() == functions.get_column_number('date'):
            editor.setDate(value)
        elif index.column() == functions.get_column_number('time'):
            editor.setTime(value)
        else:
            editor.setText(value)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def setModelData(self, editor, model, index):
        if type(editor) is FilteredComboBox:
            value = editor.currentText()
        elif index.column() == functions.get_column_number('date'):
            value = editor.date()
        elif index.column() == functions.get_column_number('time'):
            value = editor.time()
        else:
            value = editor.text()

        model.setData(index, value)


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
class DateValidator(QtGui.QValidator):
    def __init__(self):
        super(DateValidator, self).__init__()

    def validate(self, testValue, col):

        if len(testValue) < 6:
            state = QtGui.QValidator.Intermediate

        else:
            try:
                date = functions.parse_datetime_from_string(str(testValue), '00:00:00')

                if date.year() < 1900:
                    state = QtGui.QValidator.Invalid

                if date > datetime.datetime.now():
                    # Future date error
                    state = QtGui.QValidator.Invalid
                    returnInt = 3

                else:
                    state = QtGui.QValidator.Acceptable
                    displayValue = date.strftime(app_config['datetime_formats']['date']['display'])
                    returnInt = 0

            except (DatetimeError, ValueError):
                # Invalid date error
                displayValue = ""
                state = QtGui.QValidator.Invalid
                returnInt = 4




        return state, displayValue, returnInt


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
                elif testValue == "":
                    state = QtGui.QValidator.Intermediate
                    value = testValue
                    returnInt = 0
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
        """Rounds value to precision specified in column_config."""
        return round(float(input), self.decimals)


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
            elif testValue == "":
                state = QtGui.QValidator.Acceptable
                value = testValue
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


class TimeValidator(QtGui.QValidator):
    def __init__(self):
        super(TimeValidator, self).__init__()

    def validate(self, testValue, col):
        if testValue == "":
            displayValue = ""
            state = QtGui.QValidator.Acceptable
            returnInt = 0
        else:
            try:
                time = functions.parse_datetime_from_string('01/01/1900', str(testValue))
                try:
                    displayValue = time.strftime(app_config['datetime_formats']['time']['display'])
                    state = QtGui.QValidator.Acceptable
                    returnInt = 0
                except ValueError:
                    # Invalid time error
                    displayValue = testValue
                    state = QtGui.QValidator.Invalid
                    returnInt = 4
            except DatetimeError:
                # Invalid time error
                displayValue = testValue
                state = QtGui.QValidator.Invalid
                returnInt = 4

        return state, displayValue, returnInt