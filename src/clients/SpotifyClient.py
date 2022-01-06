import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config import SPOTIFY_ID
from config import SPOTIFY_SECRET


class SpotifyClient:
    def __init__(self):
        auth_manager = SpotifyClientCredentials(SPOTIFY_ID, SPOTIFY_SECRET)
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_playlist(self, playlist_id, is_sorted_by_date_added = False):
        playlist = self.sp.playlist(playlist_id)
        
        track_list = playlist["tracks"]["items"]

        #print(playlist['tracks']['limit'])
        
        if is_sorted_by_date_added:
            track_list = sorted(track_list, key=lambda t: t['added_at'], reverse=True)

        clean_list = []
        for track in track_list:
            entry = track["track"]["name"]
            for artist in track["track"]["artists"]:
                entry = entry + " - " + artist["name"]

            clean_list.append(entry)

        return clean_list

    def get_track(self, track_id):
        track = self.sp.track(track_id)
        song_name = track["name"]
        for artist in track["artists"]:
            song_name = song_name + " " + artist["name"]
        return song_name

SpotifyClient().get_playlist('31OSfeHFQAkz8cMej2chGL')