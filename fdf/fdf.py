"""
Module: mainapp.py
Runs the KiWQM Field Data Formatter GUI, used to generate a valid
field data import file for KiWQM.

Author: Daniel Harris
Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/10/2015

Classes:
MainApp: Constructor for the main application.

Functions:
Main: Runs the Field Data Formatter app.
"""

import wx
import gui


###############################################################################
# Main app constructor and initialisation
###############################################################################
class MainApp(wx.App):
    """
    Constructor for the main application
    """
    def OnInit(self):
        # Show the splash screen on app startup
        splash = gui.SplashScreen()
        splash.Show()
        # Get the app instance
        app = wx.GetApp()
        # Set the frame to be displayed
        frame = gui.LoadFrame()
        # Place the frame at the top and show it
        app.SetTopWindow(frame)
        frame.Show(True)
        return True


# -----------------------------------------------------------------------------
def main():
    """
    Run the Field Data Formatter app
    """
    app = MainApp()
    app.MainLoop()


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
