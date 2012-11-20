#!/usr/bin/python

# spotify-media-keys
#
# v0.6d (28th aug 11)
# by JonW (jon.neverwinter@gmail.com)
# patched 20110907 by Jansen Price (sumpygump@gmail.com)
# patched 20120729 by Jansen Price (sumpygump@gmail.com) and brandl.matthaeus
#
# Original by SveinT (sveint@gmail.com)
# up to v0.5.2 (27th jan 11)

import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gobject

class MediaKeyHandler():
  def __init__(self):
    self.service = None
    self.bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
    self.keys = {
      "Play"     : "PlayPause",
      "Stop"     : "Pause",
      "Pause"    : "Pause",
      "Next"     : "Next",
      "Previous" : "Previous",
    }

    self.bus_object = self.bus.get_object(
      "org.gnome.SettingsDaemon", "/org/gnome/SettingsDaemon/MediaKeys")

    self.bus_object.GrabMediaPlayerKeys(
      "Spotify", 0, dbus_interface="org.gnome.SettingsDaemon.MediaKeys")

    self.bus_object.connect_to_signal(
      "MediaPlayerKeyPressed", self.handle_key_pressed)

  def handle_key_pressed(self, *mmkeys):
    for key in mmkeys:
      if key in self.keys and self.keys[key]:
        self.execute_key(self.keys[key])

  def execute_key(self, key):
    try:
      if not self.service:
        self.service = self.bus.get_object(
          "com.spotify.qt", "/org/mpris/MediaPlayer2")

      self.service.get_dbus_method(key, "org.mpris.MediaPlayer2.Player")()
    except:
      self.service = None

if __name__ == "__main__":
  print("spotify-media-keys v0.7")

  DBusGMainLoop(set_as_default=True)
  MediaKeyHandler()
  gobject.MainLoop().run()
