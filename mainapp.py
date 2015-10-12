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
