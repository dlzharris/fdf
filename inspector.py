import wx
from ObjectListView import ObjectListView, ColumnDefn, CellEditor
from wx.lib.pubsub import pub
import functions
import globals


###############################################################################
class loadDialog (wx.Frame):

    def __init__(self, parent=None):
        # Set up the frames we will be using
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"KiWQM Field Data Import Tool",
                          pos=wx.DefaultPosition, size=wx.Size(691, 349), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)
        self.editWindow = EditWindow()

        # Set the frame size and background colour
        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK))

        # Create the sizers
        bSizer2 = wx.BoxSizer(wx.VERTICAL)
        bSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        # Introductory text
        intro_text = u"Welcome to the KiWQM Field Data Import Tool. " \
                     u"This tool will format your field data ready for importing to KiWQM. " \
                     u"To get started, select an instrument type, the sampler name, " \
                     u"and select the logger file for the instrument."
        self.m_staticText1 = wx.StaticText(self, wx.ID_ANY, intro_text, wx.DefaultPosition, wx.Size(-1,-1), wx.ALIGN_CENTRE)
        self.m_staticText1.Wrap(1500)
        bSizer2.Add(self.m_staticText1, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)

        # Instrument selection box
        m_choice_instrumentChoices = [u"Pick an instrument..."]
        m_choice_instrumentChoices.extend(globals.INSTRUMENTS)
        self.m_choice_instrument = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice_instrumentChoices, 0)
        self.m_choice_instrument.SetSelection(0)
        bSizer3.Add(self.m_choice_instrument, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Sampler selection box
        m_choice_samplerChoices = [u"Select sampler..."]
        m_choice_samplerChoices.extend(globals.FIELD_STAFF)
        self.m_choice_sampler = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice_samplerChoices, 0)
        self.m_choice_sampler.SetSelection(0)
        bSizer3.Add(self.m_choice_sampler, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Data entry mode radio box
        m_radioBox_entryModeChoices = [u"Load logger file", u"Manual data entry"]
        self.m_radioBox_entryMode = wx.RadioBox(self, wx.ID_ANY, u"Data entry mode", wx.DefaultPosition,
                                                wx.DefaultSize, m_radioBox_entryModeChoices, 2, wx.RA_SPECIFY_COLS)
        self.m_radioBox_entryMode.SetSelection(0)
        bSizer3.Add(self.m_radioBox_entryMode, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Place the selection boxes in the vertical sizer
        bSizer2.Add(bSizer3, 1, wx.EXPAND, 5)

        # File selection explanatory text
        explan_text = u"If you are importing data from a logger file, " \
                      u"select the file with the \"Browse\" button below."
        self.m_staticText2 = wx.StaticText(self, wx.ID_ANY, explan_text, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText2.Wrap(-1)
        bSizer2.Add(self.m_staticText2, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        # File browser
        self.m_filePicker1 = wx.FilePickerCtrl(self, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*",
                                               wx.DefaultPosition, wx.DefaultSize,
                                               wx.FLP_CHANGE_DIR | wx.FLP_DEFAULT_STYLE | wx.FLP_FILE_MUST_EXIST)
        bSizer2.Add(self.m_filePicker1, 0, wx.ALL | wx.EXPAND, 5)

        # Load file button
        self.m_button_loadFile = wx.Button(self, wx.ID_ANY, u"Continue", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_button_loadFile.Bind(wx.EVT_BUTTON, self.sendAndClose)
        bSizer2.Add(self.m_button_loadFile, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        # Set up the sizer and frame layout
        self.SetSizer(bSizer2)
        self.Layout()
        self.Centre(wx.BOTH)

        # Show the window
        self.Show()

    def __del__(self):
        pass

    def sendAndClose(self, event):
        path = self.m_filePicker1.GetPath()
        sampler = self.m_choice_sampler.GetStringSelection()
        instrument = self.m_choice_instrument.GetStringSelection()
        pub.sendMessage("importDataListener", message=path, sampler=sampler, instrument=instrument)
        self.editWindow.Show()
        self.Hide()


###############################################################################
# Edit window configuration
###############################################################################
class EditWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title="KiWQM Field Data Importer (Data Editing Mode)", size=(800, 600))
        panel = EditPanel(self)


class EditPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        # Set up the panel to listen for messages from the opening screen
        pub.subscribe(self.dataListener, "importDataListener")

        # Create a placeholder for the save as filename
        self.saveAsFilename = None

        # Create the ObjectListView object instance and set the instance properties
        self.dataOlv = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.dataOlv.cellEditMode = ObjectListView.CELLEDIT_SINGLECLICK  # Really only happens on double-click

        # Set the column names and column data sources
        self.setColumns()

        # Reset button
        resetBtn = wx.Button(self, wx.ID_ANY, "Reset data")
        resetBtn.Bind(wx.EVT_BUTTON, self.resetData)

        # Export button
        exportBtn = wx.Button(self, wx.ID_ANY, "Export data")
        exportBtn.Bind(wx.EVT_BUTTON, self.exportData)

        # Create sizer and add gui elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.dataOlv, 1, wx.ALL | wx.EXPAND, 5)
        mainSizer.Add(resetBtn, 0, wx.ALL | wx.CENTER, 5)
        mainSizer.Add(exportBtn, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(mainSizer)

    # -------------------------------------------------------------------------
    def dataListener(self, message, sampler=None, instrument=None):
        """
        Receives data from the load dialog and sends it to the objectlistview
        This function is triggered by a publisher-subscriber listener
        """
        # Check if the selected instrument is a valid instrument, that is
        # the selection is not the "Please select an instrument..." option in the
        # load dialog.
        if instrument in globals.INSTRUMENTS:
            pass
        else:
            instrument = globals.DEFAULT_INSTRUMENT
        # Check the instrument file and load it
        data_in_location = functions.load_instrument_file(message, instrument)
        self.dataOlv.SetObjects(data_in_location)
        # Update the sampler and instrument
        objects = self.dataOlv.GetObjects()
        for obj in objects:
            obj['sampling_officer'] = sampler
            obj['sampling_instrument'] = instrument
            self.dataOlv.RefreshObject(obj)

    # -------------------------------------------------------------------------
    def resetData(self, event):
        # TODO: Message box - Warning: all data will be lost.
        self.dataOlv.DeleteAllItems()
        # TODO: Go back to loadDialog

    # -------------------------------------------------------------------------
    def exportData(self, event):
        """
        Prepare the dictionary for export and write to csv
        """
        # Open the save as dialog
        self.onSaveFile()
        # Put the data in a dictionary for processing
        data_dicts = self.dataOlv.GetObjects()
        # TODO: Check required fields are filled
        # Reformat the data in parameter-oriented format
        data_reformatted = functions.prepare_dictionary(data_dicts)
        # Write the data to csv
        try:
            functions.write_to_csv(data_reformatted, self.saveAsFilename, globals.FIELDNAMES)
        except IOError:
            self.saveFileErrorMsg()

    # -------------------------------------------------------------------------
    def saveFileErrorMsg(self):
        wx.MessageBox("File currently in use.  Please close file to continue.", "Warning!", wx.OK | wx.ICON_EXCLAMATION)

    # -------------------------------------------------------------------------
    def updateSampleStation(self, sampleObject, value):
        """
        Tries to generate sampling number if station number has been updated
        """
        sampleObject['station_number'] = value
        if sampleObject['sample_matrix'] != "":
            sampleObject['sampling_number'] = functions.get_sampling_number(sampleObject)
        else:
            pass

    # -------------------------------------------------------------------------
    def updateSampleMatrix(self, sampleObject, value):
        """
        Tries to generate sampling number if matrix has been updated
        """
        sampleObject['sample_matrix'] = value
        if sampleObject['sample_matrix'] != "":
            sampleObject['sampling_number'] = functions.get_sampling_number(sampleObject)
        else:
            pass

    # -------------------------------------------------------------------------
    def setColumns(self, data=None):
        """
        Defines columns and associated data sources
        """
        self.dataOlv.SetColumns([
            ColumnDefn("", "center", 20, "checked"),
            ColumnDefn("MP#", "left", 80, "mp_number"),
            ColumnDefn("Station#", "center", 100, "station_number",  valueSetter=self.updateSampleStation),
            ColumnDefn("Sampling Number", "center", 220, "sampling_number", isEditable=False),
            ColumnDefn("Date", "center", 100, "date"),
            ColumnDefn("Time", "center", -1, "sample_time"),
            ColumnDefn("Loc#", "left", 80, "location_id"),
            ColumnDefn("Seq#", "left", 80, "sample_cid"),
            ColumnDefn("Rep#", "left", 50, "replicate_number"),
            ColumnDefn("Matrix", "left", 100, "sample_matrix", cellEditorCreator=dropDownComboBox, valueSetter=self.updateSampleMatrix),
            ColumnDefn("Sample Type", "left", 100, "sample_type", cellEditorCreator=dropDownComboBox),
            # ColumnDefn("Collection Method", "left", 100, "collection_method"),
            ColumnDefn("Calibration Record", "left", 100, "calibration_record"),
            ColumnDefn("Instrument", "left", 100, "sampling_instrument", cellEditorCreator=dropDownComboBox),
            ColumnDefn("Sampling Officer", "left", 100, "sampling_officer", cellEditorCreator=dropDownComboBox),
            # ColumnDefn("Event Time", "left", 100, "event_time"),
            ColumnDefn("Sample Collected", "left", 100, "sample_collected", cellEditorCreator=dropDownComboBox),
            ColumnDefn("Depth Upper (m)", "left", 100, "depth_upper"),
            ColumnDefn("Depth Lower (m)", "left", 100, "depth_lower"),
            ColumnDefn("DO (mg/L)", "left", 100, "do"),
            ColumnDefn("DO (% sat)", "left", 100, "do_sat"),
            ColumnDefn("pH", "left", 100, "ph"),
            ColumnDefn("Temp (deg C)", "left", 50, "temp_c"),
            ColumnDefn("Conductivity", "left", 100, "conductivity_uncomp"),
            ColumnDefn("Turbidity", "left", 100, "turbidity"),
            ColumnDefn("Water Depth", "left", 100, "water_depth"),
            ColumnDefn("Gauge Height (m)", "left", 100, "gauge_height"),
            ColumnDefn("Comments", "left", 200, "sampling_comment")
        ])

    def onSaveFile(self):
        """
        Create and show the Save FileDialog
        """
        wildcard = "Comma-separated values (*.csv)|*.csv"
        dlg = wx.FileDialog(
            self, message="Save file as ...",
            #defaultDir=self.currentDirectory,
            defaultFile="", wildcard=wildcard, style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.saveAsFilename = dlg.GetPath()

        dlg.Destroy()

###############################################################################
# Additional GUI components
###############################################################################
def dropDownComboBox(olv, rowIndex, columnIndex):
    """
    Return a ComboBox that lets the user choose from the appropriate values for the column.
    """
    # Get the column object
    col = olv.columns[columnIndex]
    # Set the default display style options
    style_ordered = wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_PROCESS_ENTER
    style_unordered = wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER
    style = style_ordered
    # Select the correct list for the column
    if col.title == "Matrix":
        options = globals.MATRIX_TYPES
    if col.title == "Instrument":
        options = globals.INSTRUMENTS
    if col.title == "Sample Collected":
        options = globals.BOOLEAN
        # Ensure the sample type displays in the specific order
        style = style_unordered
    if col.title == "Sampling Officer":
        options = globals.FIELD_STAFF
    if col.title == "Sample Type":
        options = globals.SAMPLE_TYPES
        # Ensure the sample type displays in the specific order
        style = style_unordered
    # Create the combobox object
    cb = wx.ComboBox(olv, choices=list(options),
                     style=style)
    # Add autocomplete to the combobox
    CellEditor.AutoCompleteHelper(cb)
    # Return the combobox object for the column
    return cb


###############################################################################
# Main loop - initiate data window
###############################################################################
def main():
    """
    Run the field data importer app
    """
    app = wx.App(False)
    frame = loadDialog()
    app.MainLoop()


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
