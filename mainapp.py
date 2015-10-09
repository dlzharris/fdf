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
