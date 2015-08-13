import wx
import functions
import globals
from ObjectListView import ObjectListView, ColumnDefn, CellEditor


class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.dataOlv = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.setSamples()

        # Allow the cell values to be edited when double-clicked
        self.dataOlv.cellEditMode = ObjectListView.CELLEDIT_SINGLECLICK

        # Format the headers
        # self.dataOlv.HeaderWordWrap = True

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

    #----------------------------------------------------------------------
    def updateControl(self, event):
        """

        """
        print "updating..."
        indata = functions.load_instrument_file("C:\\code\\projects\\field_data_importer\\sample_hydrolab_files\\hydrolab_2", "Hydrolab DS5")
        self.dataOlv.SetObjects(indata)

    def exportData(self, event):
        the_data = self.dataOlv.GetObjects()
        for item in the_data:
            print item

    def updateSampleStation(self, sampleObject, value):
        sampleObject['station_number'] = value
        if sampleObject['sample_matrix'] != "":
            sampleObject['sampling_number'] = functions.get_sampling_number(sampleObject)
        else:
            pass

    def updateSampleMatrix(self, sampleObject, value):
        sampleObject['sample_matrix'] = value
        if sampleObject['sample_matrix'] != "":
            sampleObject['sampling_number'] = functions.get_sampling_number(sampleObject)
        else:
            pass

    #----------------------------------------------------------------------
    def setSamples(self, data=None):
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
            ColumnDefn("Matrix", "left", 100, "sample_matrix", valueSetter=self.updateSampleMatrix),
            # ColumnDefn("Sample Type", "left", 100, "sample_type"),
            # ColumnDefn("Collection Method", "left", 100, "collection_method"),
            ColumnDefn("Calibration Record", "left", 100, "calibration_record"),
            ColumnDefn("Sampling Officer", "left", 100, "sampling_officer", cellEditorCreator=dropDownComboBox),
            # ColumnDefn("Event Time", "left", 100, "event_time"),
            ColumnDefn("Sample Collected", "left", 100, "sample_collected"),
            ColumnDefn("Depth Upper (m)", "left", 100, "depth_upper"),
            ColumnDefn("Depth Lower (m)", "left", 100, "depth_lower"),
            ColumnDefn("DO (mg/L)", "left", 100, "do"),
            ColumnDefn("DO (% sat)", "left", 100, "do_sat"),
            ColumnDefn("pH", "left", 100, "ph"),
            ColumnDefn("Temp (deg C)", "left", 50, "temp_c"),
            ColumnDefn("Conductivity", "left", 100, "conductivity_uncomp"),
            ColumnDefn("Turbidity", "left", 100, "turbidity"),
            ColumnDefn("Water Depth", "left", 100, "water_depth"),
            ColumnDefn("Gauge Height (m)", "left", 100, "gauge_height")
        ])


# Additional GUI components
def dropDownComboBox(olv, rowIndex, columnIndex):
    """
    Return a ComboBox that lets the user choose from the appropriate values for the column.
    """
    # Get the column object
    col = olv.columns[columnIndex]
    # Select the correct list for the column
    if col.title == "Sampling Officer":
        options = globals.FIELD_STAFF

    # Create the combobox object
    cb = wx.ComboBox(olv, choices=list(options),
                     style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_PROCESS_ENTER)
    # Add autocomplete to the combobox
    CellEditor.AutoCompleteHelper(cb)
    # Return the combobox object for the column
    return cb


########################################################################
class MainFrame(wx.Frame):
    #----------------------------------------------------------------------
    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title="ObjectListView Demo", size=(800, 600))
        panel = MainPanel(self)

########################################################################
class GenApp(wx.App):

    #----------------------------------------------------------------------
    def __init__(self, redirect=False, filename=None):
        wx.App.__init__(self, redirect, filename)

    #----------------------------------------------------------------------
    def OnInit(self):
        # create frame here
        frame = MainFrame()
        frame.Show()
        return True

#----------------------------------------------------------------------
def main():
    """
    Run the demo
    """
    app = GenApp()
    app.MainLoop()

if __name__ == "__main__":
    main()