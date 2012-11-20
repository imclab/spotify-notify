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
    self.spotifyservice = False

    self.prev = 0
    self.new = False
    self.notifyid = 0

    self.connect()

  def __del__(self):
    if SpotifyNotify and SpotifyNotify.tmpfile:
      SpotifyNotify.tmpfile.close()

  def connect(self):
    self.bus = dbus.Bus(dbus.Bus.TYPE_SESSION)

    try:
      self.spotifyservice = self.bus.get_object(
        'com.spotify.qt', '/org/mpris/MediaPlayer2')
    except Exception, e:
      self.spotifyservice = False

  def pollChange(self):
    try:
      self.spotifyservice = self.bus.get_object('com.spotify.qt', '/')
      self.cmd = self.spotifyservice.get_dbus_method(
        'GetMetadata', 'org.freedesktop.MediaPlayer2')
      self.new = self.cmd()
    except Exception, e:
      pass

    if (self.prev != self.new):
      if (self.prev):
        self.trackChange(self.new)
      self.prev = self.new

    return 1

  def trackChange(self, *trackChange):
    if not trackChange[0]:
      return

    self.prev = trackChange[0]

    trackInfo = {}
    trackMap = {
        'artist'    : 'xesam:artist',
        'album'     : 'xesam:album',
        'title'     : 'xesam:title',
        'year'      : 'xesam:contentCreated',
        'trackhash' : 'mpris:trackid',
        'arturl'    : 'mpris:artUrl'
    }

    # Fetch the track information for the notification window.
    for key in trackMap:
      if not trackMap[key] in trackChange[0]:
        continue
      piece = trackChange[0][trackMap[key]]
      if key == 'year':
        piece = str(piece[:4])
      elif isinstance(piece, list):
        piece = ", ".join(piece)

      if not isinstance(piece, str):
        piece = str(piece)

      trackInfo[key] = piece.encode('utf-8')

    # TODO cache cover image
    cover_image = self.retrieveCoverImage(trackInfo)
    if cover_image == '':
      cover_image = APPLICATION_DIR + 'icon_spotify.png'

    # Connect to notification interface on DBUS.
    self.notifyservice = self.bus.get_object(
      'org.freedesktop.Notifications', '/org/freedesktop/Notifications')
    self.notifyservice = dbus.Interface(
      self.notifyservice, "org.freedesktop.Notifications")
    notifyText = "{0}\n{1}".format(trackInfo['title'], trackInfo['album'])
    if len(trackInfo['year']) > 0:
      notifyText += " ({0})".format(trackInfo['year'])

    # The second param is the replace id, so get the notify id back,
    # store it, and send it as the replacement on the next call.
    self.notifyid = self.notifyservice.Notify(
      "spotify-notify", self.notifyid, cover_image, trackInfo['artist'],
      notifyText, [], {}, 2)

  def retrieveCoverImage(self, trackInfo):
    if 'arturl' in trackInfo:
      return self.fetchCoverImage(trackInfo['arturl'])

    return "";

  def fetchCoverImage(self, url):
    # Close the temporary image file, we are going to make a new one.
    if SpotifyNotify.tmpfile:
      SpotifyNotify.tmpfile.close()
      SpotifyNotify.tmpfile = False

    try:
      SpotifyNotify.tmpfile = tempfile.NamedTemporaryFile()
      tmpfilename = SpotifyNotify.tmpfile.name
      coverfile = urllib2.urlopen(url)
      SpotifyNotify.tmpfile.write(coverfile.read())
      SpotifyNotify.tmpfile.flush()
      return tmpfilename
    except Exception, e:
      pass

    return ""

if __name__ == "__main__":
  print("spotify-notify v0.7")

  DBusGMainLoop(set_as_default=True)
  SN = SpotifyNotify()
  gobject.timeout_add(500, SN.pollChange)
  gobject.MainLoop().run()
