#!/usr/bin/python

# spotify-notify
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
import gobject, gtk, os, tempfile, sys, time, re, urllib2

# The url to use when fetching spotify track information.
SPOTIFY_OPEN_URL = "http://open.spotify.com/track/"

# The path to this application's directory.
APPLICATION_DIR = sys.path[0] + "/"

class SpotifyNotify():
  tmpfile = False

  def __init__(self):
    self.notifyid = 0
    self.notifyservice = None
    self.bus = dbus.Bus(dbus.Bus.TYPE_SESSION)

    nameownerbus = self.bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
    nameownerbus.connect_to_signal("NameOwnerChanged", self.name_owner_changed, arg0="org.mpris.MediaPlayer2.spotify")

  def __del__(self):
    if SpotifyNotify and SpotifyNotify.tmpfile:
      SpotifyNotify.tmpfile.close()

  def get_notify_service(self, fun):
    try:
      if not self.notifyservice:
        self.notifyservice = self.bus.get_object(
          'org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        self.notifyservice = dbus.Interface(
          self.notifyservice, "org.freedesktop.Notifications")
      return fun(self.notifyservice)
    except:
      self.notifyservice = None

  def name_owner_changed(self, name, before, after):
    if after and name == "org.mpris.MediaPlayer2.spotify":
      self.spotify = self.bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
      self.spotify.connect_to_signal("PropertiesChanged", self.track_changed)

  def track_changed(self, interface, changed_props, invalidated_props):
    metadata = changed_props.get("Metadata", {})
    if not metadata:
      return

    trackInfo = {}
    trackMap = {
        'artist'    : 'xesam:artist',
        'album'     : 'xesam:album',
        'title'     : 'xesam:title',
        'year'      : 'xesam:contentCreated',
        'arturl'    : 'mpris:artUrl'
    }

    # Fetch the track information for the notification window.
    for key in trackMap:
      if not trackMap[key] in metadata:
        continue
      piece = metadata[trackMap[key]]
      if key == 'year':
        piece = str(piece[:4])
      elif isinstance(piece, list):
        piece = ", ".join(piece)

      if not isinstance(piece, str):
        piece = str(piece)

      trackInfo[key] = piece.encode('utf-8')

    cover_image = self.retrieveCoverImage(trackInfo)
    if not cover_image:
      cover_image = APPLICATION_DIR + 'icon_spotify.png'

    notifyText = "{0}\n{1}".format(trackInfo['title'], trackInfo['album'])
    if len(trackInfo['year']) > 0:
      notifyText += " ({0})".format(trackInfo['year'])

    # The second param is the replace id, so get the notify id back,
    # store it, and send it as the replacement on the next call.
    nid = self.notifyid
    self.notifyid = self.get_notify_service(
      lambda s: s.Notify("spotify-notify", nid, cover_image, trackInfo['artist'], notifyText, [], {}, 2))

  # TODO cache cover image
  def retrieveCoverImage(self, trackInfo):
    if 'arturl' in trackInfo:
      return self.fetchCoverImage(trackInfo['arturl'])
    return "";

  def fetchCoverImage(self, url):
    # Close the temporary image file, we are going to make a new one.
    if SpotifyNotify.tmpfile:
      SpotifyNotify.tmpfile.close()
      SpotifyNotify.tmpfile = None

    try:
      SpotifyNotify.tmpfile = tempfile.NamedTemporaryFile()
      tmpfilename = SpotifyNotify.tmpfile.name
      coverfile = urllib2.urlopen(url)
      SpotifyNotify.tmpfile.write(coverfile.read())
      SpotifyNotify.tmpfile.flush()
      return tmpfilename
    except Exception, e:
      return ""

if __name__ == "__main__":
  print("spotify-notify v0.7")

  DBusGMainLoop(set_as_default=True)
  SpotifyNotify()
  gobject.MainLoop().run()
