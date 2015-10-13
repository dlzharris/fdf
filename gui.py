"""
Module: gui.py
Defines the classes and methods for the GUI portion of the KiWQM Field
Data Formatter.

Author: Daniel Harris
Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/10/2015

Classes:
LoadFrame: Initialises window for the opening load screen.
LoadPanel: Constructs GUI elements for load screen.
EditFrame: Initialises window for the editing screen.
EditPanel: Constructs GUI elements for the editing screen.
SplashScreen: Displays the splash screen on app load.
HelpHTML: Initialises window for the help dialog.
HTMLWindow: Behaviours for the HTML code in the help dialog.
Menus: Constructs and displays the menu bar and menu items.
"""
# Standard Python packages
import webbrowser
# wx widgets
import wx
import wx.html
from wx.lib.pubsub import pub
from wx.lib.wordwrap import wordwrap
# Custom wx objects
from ObjectListView import ObjectListView, ColumnDefn, CellEditor
# Local packages
import functions
import globals
import help


###############################################################################
# Load Window (Main Frame)
###############################################################################
class LoadFrame (wx.Frame):
    """
    Initialise the window for the opening load screen.
    """
    def __init__(self, parent=None):
        # Set up the frames we will be using
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"KiWQM Field Data Formatter",
                          pos=wx.DefaultPosition, size=wx.Size(691, 349), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)
        self.panel = LoadPanel(self)
        # Set the frame size and background colour
        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)
        self.Centre(wx.BOTH)
        # Create the menu bar
        Menus(self)
        # Show the window
        self.Show()

    # -------------------------------------------------------------------------
    def __del__(self):
        pass

    # -------------------------------------------------------------------------
    def OnClose(self, event):
        self.Close()


class LoadPanel (wx.Panel):
    """
    Construct the GUI elements for the load screen.
    """
    def __init__(self, parent):
        # Set up the panel
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.parent = parent
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK))

        # Set the edit window (opens after closing the load window)
        self.EditWindow = EditFrame()

        # Set up the load panel's objects
        # Create the sizers
        SizerVertical = wx.BoxSizer(wx.VERTICAL)
        SizerHorizontal = wx.BoxSizer(wx.HORIZONTAL)

        # Introductory text
        TextIntroduction = u"Welcome to the KiWQM Field Data Formatter. " \
                           u"This tool will format your field data ready for importing to KiWQM. " \
                           u"To get started, select an instrument type, the sampler name, " \
                           u"and select the logger file for the instrument."
        self.StaticTextIntroduction = wx.StaticText(self, wx.ID_ANY, TextIntroduction, wx.DefaultPosition, wx.Size(-1,-1), wx.ALIGN_CENTRE)
        self.StaticTextIntroduction.Wrap(1500)
        SizerVertical.Add(self.StaticTextIntroduction, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)

        # Instrument selection box
        MultiChoiseInstrumentsList = [u"Pick an instrument..."]
        MultiChoiseInstrumentsList.extend(globals.INSTRUMENTS)
        self.MultiChoiceInstrumentsSelection = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, MultiChoiseInstrumentsList, 0)
        self.MultiChoiceInstrumentsSelection.SetSelection(0)
        SizerHorizontal.Add(self.MultiChoiceInstrumentsSelection, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Sampler selection box
        MultiChoiceSamplersList = [u"Select sampler..."]
        MultiChoiceSamplersList.extend(globals.FIELD_STAFF)
        self.MultiChoiceSamplersSelection = wx.Choice(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, MultiChoiceSamplersList, 0)
        self.MultiChoiceSamplersSelection.SetSelection(0)
        SizerHorizontal.Add(self.MultiChoiceSamplersSelection, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Data entry mode radio box
        RadioBoxEntryModeList = [u"Load logger file", u"Manual data entry"]
        self.RadioBoxEntryModeSelection = wx.RadioBox(self, wx.ID_ANY, u"Data entry mode", wx.DefaultPosition,
                                                wx.DefaultSize, RadioBoxEntryModeList, 2, wx.RA_SPECIFY_COLS)
        self.RadioBoxEntryModeSelection.SetSelection(0)
        SizerHorizontal.Add(self.RadioBoxEntryModeSelection, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Place the selection boxes in the vertical sizer
        SizerVertical.Add(SizerHorizontal, 1, wx.EXPAND, 5)

        # File selection explanatory text
        TextExplanation = u"If you are importing data from a logger file, " \
                          u"select the file with the \"Browse\" button below."
        self.StaticTextExplanation = wx.StaticText(self, wx.ID_ANY, TextExplanation, wx.DefaultPosition, wx.DefaultSize, 0)
        self.StaticTextExplanation.Wrap(-1)
        SizerVertical.Add(self.StaticTextExplanation, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        # File browser
        self.FilePicker = wx.FilePickerCtrl(self, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*",
                                               wx.DefaultPosition, wx.DefaultSize,
                                               wx.FLP_CHANGE_DIR | wx.FLP_DEFAULT_STYLE | wx.FLP_FILE_MUST_EXIST)
        SizerVertical.Add(self.FilePicker, 0, wx.ALL | wx.EXPAND, 5)

        # Load file button
        self.ButtonLoadFile = wx.Button(self, wx.ID_ANY, u"Continue", wx.DefaultPosition, wx.DefaultSize, 0)
        self.ButtonLoadFile.Bind(wx.EVT_BUTTON, self.SendAndClose)
        SizerVertical.Add(self.ButtonLoadFile, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        # Set up the sizer and frame layout
        self.SetSizer(SizerVertical)
        self.Layout()

    # -------------------------------------------------------------------------
    def SendAndClose(self, event):
        """
        Send the data from the load screen to the DataListener in the
        edit screen.
        """
        # Check input mode
        InputMode = self.RadioBoxEntryModeSelection.GetSelection()
        # Load from file
        if InputMode == 0:
            path = self.FilePicker.GetPath()
            if path == "":
                wx.MessageBox("Please select a valid file or switch to manual mode.", "No file specified.",
                              wx.OK | wx.ICON_EXCLAMATION)
                return None
        # Manual data entry
        else:
            path = None
        # Generic components
        sampler = self.MultiChoiceSamplersSelection.GetStringSelection()
        instrument = self.MultiChoiceInstrumentsSelection.GetStringSelection()
        # Publish data to listener
        pub.sendMessage("importDataListener", path=path, sampler=sampler, instrument=instrument)
        # Show the edit window and hide the load dialog
        self.EditWindow.Show()
        self.parent.Hide()


###############################################################################
# Edit window configuration
###############################################################################
class EditFrame(wx.Frame):
    """
    Initialise the window for the editing screen.
    """
    def __init__(self):
        # Set up the frames we will be using
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title="KiWQM Field Data Formatter (Data Editing Mode)", size=(1000, 600))
        self.panel = EditPanel(self)
        # Create the menu bar
        Menus(self)

    # -------------------------------------------------------------------------
    def OnClose(self, event):
        self.Close()


class EditPanel(wx.Panel):
    """
    Construct the GUI elements for the editing screen.
    """
    def __init__(self, parent):
        # Set up the panel
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.parent = parent

        # Set the panel to listen for messages from the opening screen
        pub.subscribe(self.DataListener, "importDataListener")

        # Create a placeholder for the save as filename
        self.SaveAsFilename = None

        # Create the ObjectListView object instance and set the instance properties
        self.DataContainer = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.DataContainer.cellEditMode = ObjectListView.CELLEDIT_SINGLECLICK  # Really only happens on double-click

        # Set the column names and column data sources
        self.SetColumns()

        # Reset button
        ButtonReset = wx.Button(self, wx.ID_ANY, "Reset data")
        ButtonReset.Bind(wx.EVT_BUTTON, self.ResetData)

        # Export button
        ButtonExport = wx.Button(self, wx.ID_ANY, "Export data")
        ButtonExport.Bind(wx.EVT_BUTTON, self.ExportData)

        # Create sizer and add gui elements
        SizerMain = wx.BoxSizer(wx.VERTICAL)
        SizerMain.Add(self.DataContainer, 1, wx.ALL | wx.EXPAND, 5)
        SizerMain.Add(ButtonReset, 0, wx.ALL | wx.CENTER, 5)
        SizerMain.Add(ButtonExport, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(SizerMain)

    # -------------------------------------------------------------------------
    def DataListener(self, path, sampler=None, instrument=None):
        """
        Receive data from the load dialog and send it to the
        Objectlistview data container. This function is triggered by a
        publisher-subscriber listener.
        """
        # Check if the selected instrument is a valid instrument, that is
        # the selection is not the "Please select an instrument..." option in the
        # load dialog.
        if instrument in globals.INSTRUMENTS:
            pass
        else:
            instrument = globals.DEFAULT_INSTRUMENT

        # If a file path is provided, open it. If no path is provided, then we
        # are entering manual entry mode, so we need to create blank lines in
        # the table.
        if path is not None:
            # Load mode: Check the instrument file and load it
            DataToLoad = functions.load_instrument_file(path, instrument)
        else:
            # Manual mode: Ask the user for the number of lines (samples) required
            TextValid = False
            while TextValid is False:
                TxtDlgNumberLines = wx.TextEntryDialog(self,
                                                       message="Enter the number of samples below:",
                                                       caption="Data entry set-up",
                                                       defaultValue="5")
                # When OK button is clicked
                if TxtDlgNumberLines.ShowModal() == wx.ID_OK:
                    NumberLines = TxtDlgNumberLines.GetValue()
                    try:
                        DataToLoad = functions.load_manual_entry(int(NumberLines))
                        TextValid = True
                    except ValueError:
                        wx.MessageBox(message="Please enter a valid number!",
                                      caption="Invalid number!",
                                      style=wx.OK | wx.ICON_EXCLAMATION)

        # Update the sampler and instrument
        self.DataContainer.SetObjects(DataToLoad)
        objects = self.DataContainer.GetObjects()
        for obj in objects:
            obj['sampling_officer'] = sampler
            obj['sampling_instrument'] = instrument
            self.DataContainer.RefreshObject(obj)

    # -------------------------------------------------------------------------
    def SetColumns(self, data=None):
        """
        Define columns and associated data sources.
        """
        self.DataContainer.SetColumns([
            ColumnDefn("", "center", 20, "checked"),
            ColumnDefn("MP#", "left", 60, "mp_number"),
            ColumnDefn("Station#", "center", 90, "station_number",
                       valueSetter=self.UpdateSampleStation),
            ColumnDefn("Sampling ID", "center", 140, "sampling_number",
                       isEditable=False),
            ColumnDefn("Date", "center", -1, "date"),
            ColumnDefn("Time", "center", -1, "sample_time"),
            ColumnDefn("Loc#", "left", 50, "location_id"),
            ColumnDefn("Seq#", "left", 50, "sample_cid"),
            ColumnDefn("Matrix", "left", 60, "sample_matrix",
                       cellEditorCreator=self.DropDownComboBox),
            ColumnDefn("Sample Type", "left", 100, "sample_type",
                       cellEditorCreator=self.DropDownComboBox,
                       valueSetter=self.UpdateSampleType),
            # ColumnDefn("Collection Method", "left", 100, "collection_method"),
            ColumnDefn("Calibration Record", "left", 140, "calibration_record"),
            ColumnDefn("Instrument", "left", 110, "sampling_instrument",
                       cellEditorCreator=self.DropDownComboBox),
            ColumnDefn("Sampling Officer", "left", 125, "sampling_officer",
                       cellEditorCreator=self.DropDownComboBox),
            ColumnDefn("Sample Collected", "left", 130, "sample_collected",
                       cellEditorCreator=self.DropDownComboBox),
            ColumnDefn("Depth Upper (m)", "left", 125, "depth_upper"),
            ColumnDefn("Depth Lower (m)", "left", 125, "depth_lower"),
            ColumnDefn("DO (mg/L)", "left", 85, "do"),
            ColumnDefn("DO (% sat)", "left", 85, "do_sat"),
            ColumnDefn("pH", "left", 50, "ph"),
            ColumnDefn("Temp (deg C)", "left", 110, "temp_c"),
            ColumnDefn("EC (uS/cm)", "left", 90, "conductivity_uncomp"),
            ColumnDefn("Turbidity (NTU)", "left", 120, "turbidity"),
            ColumnDefn("Water Depth (m)", "left", 130, "water_depth"),
            ColumnDefn("Gauge Height (m)", "left", 135, "gauge_height"),
            ColumnDefn("Comments", "left", 200, "sampling_comment")
        ])

    # -------------------------------------------------------------------------
    def DropDownComboBox(self, olv, RowIndex, ColumnIndex):
        """
        Return a ComboBox that lets the user choose from the appropriate values for the column.
        """
        # Get the column object
        col = olv.columns[ColumnIndex]
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
        ComboBox = wx.ComboBox(olv, choices=list(options), style=style)
        # Add autocomplete to the combobox
        CellEditor.AutoCompleteHelper(ComboBox)
        # Return the combobox object for the column
        return ComboBox

    # -------------------------------------------------------------------------
    def UpdateSampleStation(self, SampleObject, value):
        """
        Try to generate sampling number if station number has been updated.
        """
        SampleObject['station_number'] = value
        SampleObject['sampling_number'] = functions.get_sampling_number(SampleObject)

    # -------------------------------------------------------------------------
    def UpdateSampleType(self, SampleObject, value):
        """
        Try to generate sampling number if matrix has been updated.
        """
        SampleObject['sample_type'] = value
        if SampleObject['station_number'] != "":
            SampleObject['sampling_number'] = functions.get_sampling_number(SampleObject)
        else:
            pass

    # -------------------------------------------------------------------------
    def ResetData(self, event):
        """
        Confirm a data reset with the user, close the edit window and
        reopen the load dialog.
        """
        msg = "All current data will be lost. Do you want to continue?"
        dlg = wx.MessageDialog(parent=None, message=msg, caption="Confirm reset!", style=wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION)
        result = dlg.ShowModal()
        # Close the reset data dialog box
        dlg.Destroy()
        # If the reset is confirmed, clear data, close window and return to the load screen.
        if result == wx.ID_OK:
            self.DataContainer.DeleteAllItems()
            LoadDlg = LoadFrame()
            self.parent.Destroy()
            LoadDlg.Show()

    # -------------------------------------------------------------------------
    def ExportData(self, event):
        """
        Prepare the dictionary for export and write to csv.
        """
        # Put the data in a dictionary for processing
        data_dicts = self.DataContainer.GetObjects()
        # Check the data for completeness and validity
        incomplete_fields = functions.check_data_completeness(data_dicts)
        zero_value_fields = functions.check_data_zero_values(data_dicts)
        if incomplete_fields:
            self.CheckCompletenessMsg(incomplete_fields)
            return None
        if zero_value_fields:
            self.CheckZeroValuesMsg(zero_value_fields)
            return None
        # Open the save as dialog
        self.OnSaveFile()
        # Reformat the data in parameter-oriented format
        data_reformatted = functions.prepare_dictionary(data_dicts)
        # Write the data to csv
        try:
            functions.write_to_csv(data_reformatted, self.SaveAsFilename, globals.FIELDNAMES)
        except IOError:
            self.SaveFileErrorMsg()

    # -------------------------------------------------------------------------
    def CheckCompletenessMsg(self, incomplete_fields):
        """
        Display a message to the user if there are required fields that
        have been left incomplete.
        """
        msg = "The following fields have incomplete values:\n\n%s\n\nPlease complete before continuing." \
              % '\n'.join(incomplete_fields)
        wx.MessageBox(message=msg,
                      caption="Incomplete data!",
                      style=wx.OK | wx.ICON_EXCLAMATION)

    # -------------------------------------------------------------------------
    def CheckZeroValuesMsg(self, zero_value_fields):
        """
        Display a message to the user if there are parameter values
        of zero in the data set.
        """
        msg = "The following fields have items with values of zero (0):\n\n%s\n\n" \
              "A value of zero generally indicates a sensor failure, or a non-measured parameter.\n" \
              "Please review and adjust before continuing." \
              % '\n'.join(zero_value_fields)
        wx.MessageBox(message=msg,
                      caption="Data quality error!",
                      style=wx.OK | wx.ICON_EXCLAMATION)

    # -------------------------------------------------------------------------
    def OnSaveFile(self):
        """
        Create and show the Save FileDialog.
        """
        wildcard = "Comma-separated values (*.csv)|*.csv"
        SaveDialog = wx.FileDialog(self,
                                   message="Save file as ...",
                                   # defaultDir=self.currentDirectory,
                                   defaultFile="",
                                   wildcard=wildcard,
                                   style=wx.SAVE | wx.OVERWRITE_PROMPT)
        # When OK button is clicked
        if SaveDialog.ShowModal() == wx.ID_OK:
            self.SaveAsFilename = SaveDialog.GetPath()
        # Destroy the save file dialog
        SaveDialog.Destroy()

    # -------------------------------------------------------------------------
    def SaveFileErrorMsg(self):
        """
        Display an error message to the user if the attempted save
        location is currently in use.
        """
        wx.MessageBox(message="File currently in use.  Please close file to continue.",
                      caption="Warning!",
                      style=wx.OK | wx.ICON_EXCLAMATION)


###############################################################################
# Splash screen
###############################################################################
class SplashScreen(wx.SplashScreen):
    """
    Create a splash screen to display prior to app initialisation.
    """
    def __init__(self, parent=None):
        # Set splash screen variables
        SplashImage = wx.Image(name="splash_screen_scribus_01beta.jpg").ConvertToBitmap()
        SplashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        SplashDuration = 2000  # milliseconds
        # Call the splash screen constructor
        wx.SplashScreen.__init__(self,
                                 bitmap=SplashImage,
                                 splashStyle=SplashStyle,
                                 milliseconds=SplashDuration,
                                 parent=parent)
        # On splash screen close
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        wx.Yield()

    # -----------------------------------------------------------------------------
    def OnExit(self, evt):
        # Hide the splash screen
        self.Hide()
        evt.Skip()


###############################################################################
# HTML Help
###############################################################################
class HelpHTML(wx.Frame):
    """
    Initialise the window for the help dialog.
    """
    def __init__(self, parent):
        # Construct the frame
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title="About", size=(600, 700))
        # Set the frame to display HTML
        html = HTMLWindow(self)
        # Grab the HTML code and display the page
        html.SetPage(help.page)


class HTMLWindow(wx.html.HtmlWindow):
    """
    Behaviours for HTML code in help dialog.
    """
    def OnLinkClicked(self, link):
        # Get the link that was clicked
        a = link.GetHref()
        # If the link was an HTML anchor to an internal header,
        # go to the header, otherwise open the link in a browser.
        if a.startswith('#'):
            self.base_OnLinkClicked(link)
        else:
            webbrowser.open(a)


#######################################################################
# Menus
#######################################################################
class Menus(wx.MenuBar):
    """
    Create the application menus.
    """
    def __init__(self, frame):
        # Construct the menu bar
        wx.MenuBar.__init__(self)
        self.panel = frame.panel
        # Create the file menu, add items and add it to the menu bar
        FileMenu = wx.Menu()
        FileMenuItemClose = FileMenu.Append(wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, frame.OnClose, FileMenuItemClose)
        self.Append(FileMenu, "&File")
        # Create the help menu, add items and add it to the menu bar
        HelpMenu = wx.Menu()
        HelpMenuItemAbout = HelpMenu.Append(wx.ID_ABOUT)
        HelpMenuItemHelp = HelpMenu.Append(wx.ID_HELP)
        self.Bind(wx.EVT_MENU, self.OnAboutDialog, HelpMenuItemAbout)
        self.Bind(wx.EVT_MENU, self.OnHelpDialog, HelpMenuItemHelp)
        self.Append(HelpMenu, "&Help")
        # Add the menu bar to the frame
        frame.SetMenuBar(self)

    # -------------------------------------------------------------------------
    def OnHelpDialog(self, event):
        """
        Invoke an instance of the HelpHTML window and display it.
        """
        HelpDialog = HelpHTML(None)
        HelpDialog.Show()

    # -------------------------------------------------------------------------
    def OnAboutDialog(self, event):
        """
        Invoke an instance of the About dialog box and display it.
        """
        # Create an About instance
        info = wx.AboutDialogInfo()
        # Set the properties of the About box
        info.Name = "KiWQM Field Data Formatter"
        info.Version = "0.1 Beta"
        info.Copyright = "(C) 2015 DPI Water"
        info.Description = wordwrap("KiWQM Field Data Formatter formats field water quality data into a CSV file "
                                    "suitable for import to the KiWQM database.", 350, wx.ClientDC(self.panel))
        info.Developers = [wordwrap("Daniel Harris (Data & Procedures Officer, DPI Water)", 250, wx.ClientDC(self.panel))]
        # Show the About box
        wx.AboutBox(info)
