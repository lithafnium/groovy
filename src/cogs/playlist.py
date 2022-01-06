import datetime
import discord

from typing import List
from discord.ext import commands

from src.clients.AstraClient import AstraClient

from src.classes.Logger import print_log
from src.classes.YTDLSource import YTDLSource
from src.classes.MusicPlayer import MusicPlayer


class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.astra = AstraClient()

    def add_playlist(self, playlist_name: str, tracks: List[str], guild_id: str):
        playlist_id = self.astra.get_timeuuid()
        playlist_definition = {
            "playlist_tid": f"{playlist_id}",
            "guild_id": guild_id,
        }
        self.astra.add_row("playlists", playlist_definition)

    def add_track(self, track_name: str, playlist_id):
        now = datetime.datetime.now()
        track_definition = {
            "playlist_tid": f"{playlist_id}",
            "added": f"{now}",
            "song_name": track_name,
        }
        self.astra.add_row("playlist_tracks", track_definition)


def setup(bot):
    bot.add_cog(Playlist(bot))
