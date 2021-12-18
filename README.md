# WallSpot
A simple program to display current playing from Spotify app on your desktop

![](https://raw.githubusercontent.com/nanna7077/WallSpot/main/wallspot.gif)

## How to Use:
### Linux:

*Currently Supports GNOME and KDE. If you want to support your Desktop Environment and know how to set wallpaper via command line, please create an issue.*

Download the installer [from here](https://github.com/nanna7077/WallSpot/releases/download/release/wallspotInstaller.sh) and go to the path where you downloaded the installer to and do

```chmod +x wallspotInstaller.sh```

and

```./wallspotInstaller.sh```

Now you can find a menu entry named "WallSpot" in your applications menu.

You can close the program by right clicking on the tray icon and clicking Exit.

#### Dependencies:

The program requires ```pillow``` and ```pystray``` to work. It tries to install these dependencies on its own (requires internet), if it can't, it would not launch and you can manually install them by

```pip install pillow```

and

```pip install pystray```

### Windows:

Support for Windows is a Work In Progress. Please check this out in a few days.

Inspired by: [Blueberry](https://github.com/newpolygons/Blueberry)
