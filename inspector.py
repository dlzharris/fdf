import wx
import functions
import globals
from ObjectListView import ObjectListView, ColumnDefn, CellEditor


###############################################################################
# Main panel configuration
###############################################################################
class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.dataOlv = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.setSamples()

        # Allow the cell values to be edited when double-clicked
        self.dataOlv.cellEditMode = ObjectListView.CELLEDIT_SINGLECLICK

        #TODO: Remove update button. Replace with reset button
        # create an update button
        updateBtn = wx.Button(self, wx.ID_ANY, "Update OLV")
        updateBtn.Bind(wx.EVT_BUTTON, self.updateControl)

        # export button
        exportBtn = wx.Button(self, wx.ID_ANY, "Export data")
        exportBtn.Bind(wx.EVT_BUTTON, self.exportData)

        # Create some sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.dataOlv, 1, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(updateBtn, 0, wx.ALL|wx.CENTER, 5)
        mainSizer.Add(exportBtn, 0, wx.ALL|wx.CENTER, 5)
        self.SetSizer(mainSizer)

    #--------------------------------------------------------------------------
    def updateControl(self, event):
        # TODO: Replace this with data sourced from initial screen
        print "updating..."
        indata = functions.load_instrument_file("C:\\code\\projects\\field_data_importer\\sample_hydrolab_files\\hydrolab_test", "Hydrolab DS5")
        self.dataOlv.SetObjects(indata)

    def exportData(self, event):
        # TODO: Replace contents of this function by sending to write_to_csv function
        the_data = self.dataOlv.GetObjects()
        data_reformatted = functions.prepare_dictionary(the_data)
        for item in data_reformatted:
            print item


    def updateSampleStation(self, sampleObject, value):
        """
        Tries to generate sampling number if station number has been updated
        """
        sampleObject['station_number'] = value
        if sampleObject['sample_matrix'] != "":
            sampleObject['sampling_number'] = functions.get_sampling_number(sampleObject)
        else:
            pass

    def updateSampleMatrix(self, sampleObject, value):
        """
        Tries to generate sampling number if matrix has been updated
        """
        sampleObject['sample_matrix'] = value
        if sampleObject['sample_matrix'] != "":
            sampleObject['sampling_number'] = functions.get_sampling_number(sampleObject)
        else:
            pass

    #--------------------------------------------------------------------------
    def setSamples(self, data=None):
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
    style = wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_PROCESS_ENTER
    style_unordered = wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER
    # Select the correct list for the column
    if col.title == "Matrix":
        options = globals.MATRIX_TYPES
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
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title="ObjectListView Demo", size=(800, 600))
        panel = MainPanel(self)


###############################################################################
class GenApp(wx.App):
    def __init__(self, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        # create frame here
        frame = MainFrame()
        frame.Show()
        return True


###############################################################################
# Main loop - initiate data window
###############################################################################
def main():
    """
    Run the demo
    """
    app = GenApp()
    app.MainLoop()

if __name__ == "__main__":
    main()
