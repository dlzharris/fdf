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
        Splash = gui.SplashScreen()
        Splash.Show()
        return True


# -----------------------------------------------------------------------------
def main():
    """
    Run the Field Data Formatter app
    """
    # Comment the following 2 lines when ready to use the splash screen
    #app = wx.App(False)
    #frame = loadDialog()
    # Uncomment the following when ready to use the splash screen
    app = MainApp()
    app.MainLoop()


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
