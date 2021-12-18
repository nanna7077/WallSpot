import os
try:
    from PIL import Image, ImageDraw, ImageFont
except:
    print("Pillow not found. Trying to install...")
    x=os.system("python -m pip install pillow")
    if x!=0:
        print("Could not install pillow.")
        exit()
    else:
        from PIL import Image, ImageDraw, ImageFont
try:
    import pystray
except:
    print("Pystray not found. Trying to install...")
    x=os.system("python -m pip install pystray")
    if x!=0:
        print("Could not install pystary.")
        exit()
    else:
        import pystray
from threading import Thread
from subprocess import check_output
import requests
from shutil import copyfileobj
from random import randint
from tempfile import gettempdir
from functools import partial
import signal

def stripSpecialChars(string):
    return ''.join(e for e in string if (e.isalnum() or e.isspace() or e=="&"))

def getSeparator():
    if os.name=="nt":
        return "\\"
    else:
        return "/"

def getConfigFolderPath():
    if os.name=="posix":
        return os.path.expanduser("~")+"/.WallSpot"

def getDesktopEnv():
    os.system("""echo $(ps -e | grep -E -i "xfce|kde|gnome") > /tmp/WallSpot.file""")
    parseStr = ''
    with open("/tmp/WallSpot.file") as f:
        parseStr = f.read()
    os.remove("/tmp/WallSpot.file")
    de = {}
    de['kde'] = parseStr.lower().count("kde")
    de['gnome'] = parseStr.lower().count('gnome')
    de['xfce'] = parseStr.lower().count('xfce')
    # Add more
    return max(de, key=de.get)

def add_corners(im, rad=100):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, "white")
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

def get_dominant_color(in_img, palette_size=16):
    img = in_img.copy()
    img.thumbnail((100, 100))
    paletted = img.convert('P', palette=Image.ADAPTIVE, colors=palette_size)
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    palette_index = color_counts[0][1]
    dominant_color = palette[palette_index*3:palette_index*3+3]
    return dominant_color

def restore(*args):
    if os.path.exists(getConfigFolderPath()):
        if os.path.exists(getConfigFolderPath()+"/backup"):
            try:
                os.system("gsettings set org.gnome.desktop.background picture-uri file://{}".format(getConfigFolderPath()+"/backup"))
            except:
                print("[ERROR] Could not restore old wallpaper.")
        else:
            print("[ERROR] Wallpaper backup not found.")
    else:
        print("[ERROR] Could not find application folder.")
    return False

def backup():
    if not getConfigFolderPath():
        os.mkdir(getConfigFolderPath())
    currentWallpaperPath=(check_output("gsettings get org.gnome.desktop.background picture-uri", shell=True, text=True)).strip().strip("\'")
    if "WallSpot" in currentWallpaperPath:
        return
    wallpaperFile=open(currentWallpaperPath, 'rb')
    backupFile=open(getConfigFolderPath()+"/backup", 'wb')
    backupFile.write(wallpaperFile.read())
    wallpaperFile.close()
    backupFile.close()

def get_info_linux():
    import dbus
    try:
        if not hasattr(get_info_linux, "session_bus"):
            get_info_linux.session_bus = dbus.SessionBus()
        try:
            spotify_bus=get_info_linux.session_bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
            spotify_properties=dbus.Interface(spotify_bus, "org.freedesktop.DBus.Properties")
            metadata=spotify_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")
        except:
            return "APP_CLOSED"
        try:
            status=(spotify_properties.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus"))
        except:
            return "APP_CLOSED"
        if status.lower() != "playing" and status.lower() != "paused":
            return "APP_CLOSED"
        try:
            track=str(metadata["xesam:title"])
            artist=str(metadata["xesam:artist"][0])
            album=str(metadata["xesam:album"])
            arturl=str(metadata["mpris:artUrl"])
            status=status.lower().capitalize()
        except:
            return "APP_CLOSED"
        return track, artist, album, arturl, status
    except:
        return "APP_CLOSED"

def setWallpaper(path):
    if os.name=="posix":
        if desktopEnv== "gnome":
            os.system("gsettings set org.gnome.desktop.background picture-uri file://{}".format(path))
        elif desktopEnv == "kde":
            import dbus
            plugin = 'org.kde.image'
            jscript = """
            var allDesktops = desktops();
            print (allDesktops);
            for (i=0;i<allDesktops.length;i++) {
                d = allDesktops[i];
                d.wallpaperPlugin = "%s";
                d.currentConfigGroup = Array("Wallpaper", "%s", "General");
                d.writeConfig("Image", "file://%s")
            }
            """
            bus = dbus.SessionBus()
            plasma = dbus.Interface(bus.get_object('org.kde.plasmashell', '/PlasmaShell'), dbus_interface='org.kde.PlasmaShell')
            plasma.evaluateScript(jscript % (plugin, plugin, path))
        else:
            print("Desktop Environment not yet supported. Please create an issue at Wallux-Desktop repository to get support!")
            return
    else:
        import ctypes
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 0)

def stopApp():
    restore()
    os.kill(os.getpid(), signal.SIGKILL)

trayIcon=Image.new('RGB', (512, 512), (29, 185, 84))
icon=pystray.Icon('WallSpot is running')
icon.icon=trayIcon
icon.menu=pystray.Menu(pystray.MenuItem("WallSpot is running.", lambda: None), pystray.MenuItem("Exit", stopApp))
trayiconThread=Thread(target=partial(icon.run))
trayiconThread.setName("WallSpotTrayIconThread")
trayiconThread.daemon=True
trayiconThread.start()

backup()
signal.signal(signal.SIGINT, restore)
signal.signal(signal.SIGTERM, restore)

if os.name=='posix':
    desktopEnv=getDesktopEnv()
lasttitle=''
laststatus=''
imageFont22Bold=ImageFont.truetype("res/Montserrat-SemiBold.ttf", 22)
imageFont30Bold=ImageFont.truetype("res/Montserrat-SemiBold.ttf", 30)
imageFont20=ImageFont.truetype("res/Montserrat-Regular.ttf", 20)

while True:
    if os.name=='posix':
        ret=get_info_linux()
        if type(ret)==tuple:
            trackname, artist, album, arturl, status=ret
        else:
            restore()
            continue
        trackname=trackname
        artist=stripSpecialChars(" ".join(artist.split(" ")[:4]))
        album=stripSpecialChars(" ".join(album.split(" ")[:4]))
    if not (lasttitle!=trackname or laststatus!=status):
        continue
    if trackname=="Advertisement":
        restore()
        continue
    lasttitle=trackname
    laststatus=status
    widgetImage=None
    AlbumArt=None
    restore()
    try:
        for (root, dirs, file) in os.walk(getConfigFolderPath()):
            for i in file:
                if "current" in i:
                    os.remove(root+getSeparator()+i)
    except:
        pass
    try:
        r=requests.get(arturl, stream=True)
        if r:
            albumArtFilePath=gettempdir()+getSeparator()+arturl.split("/")[-1]+"."+r.headers['content-type'].split("/")[0]
            with open(albumArtFilePath, 'wb') as f:
                copyfileobj(r.raw, f)
            imagefile=albumArtFilePath
        else:
            imagefile=os.path.abspath(os.getcwd()+getSeparator()+"res/shrug.png")
    except:
        imagefile=os.path.abspath(os.getcwd()+getSeparator()+"res/shrug.png")
    AlbumArt=Image.open(imagefile)
    widgetImage = Image.open(os.path.abspath(os.getcwd())+getSeparator()+"res/rectWidget.png")
    background = Image.open(getConfigFolderPath()+getSeparator()+"backup")
    DomFill=tuple(get_dominant_color(AlbumArt))
    widgetImage.paste(DomFill, widgetImage)
    widget=ImageDraw.Draw(widgetImage)
    widget.text(xy=(405, 105), text="Now {}".format(status), font=imageFont20, fill=(255, 255, 255))
    if len(trackname)<16:
        widget.text(xy=(405, 136), text=trackname, font=imageFont30Bold, fill=(255, 255, 255), stroke_fill=(175, 175, 175), stroke_width=1)
    else:
        trackname=" ".join(trackname.split(" ")[:6])
        widget.text(xy=(405, 139), text=trackname, font=imageFont22Bold, fill=(255, 255, 255), stroke_fill=(175, 175, 175), stroke_width=1)
    widget.text(xy=(405, 180), text=album, font=imageFont20, fill=(255, 255, 255))
    widget.text(xy=(405, 210), text=artist, font=imageFont20, fill=(255, 255, 255))
    bgWidth, bgHeight=background.size
    wWidth, wHeight=widgetImage.size
    AlbumArt=AlbumArt.resize((350, 310))
    AlbumArtDraw=ImageDraw.Draw(AlbumArt)
    AlbumArt=add_corners(AlbumArt, 15)
    widgetImage.paste(AlbumArt, (45, 48))
    background.paste(widgetImage, ((bgWidth-wWidth)//2, (bgHeight-wHeight)//2), widgetImage)
    path=getConfigFolderPath()+getSeparator()+"current{}.png".format(randint(1, 100))
    background.save(path)
    setWallpaper(path)
    #widgetImage.save(os.path.expanduser("~")+"/.WallSpot"+"/current.png")