from clients.SpotifyClient import SpotifyClient

import discord
from discord.ext import commands

from classes.Logger import print_log
from classes.MusicPlayer import MusicPlayer

#test imports
from classes.MusicQueue import MusicQueue

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
        print_log(self.bot.voice_clients)

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, url=None):
        await ctx.trigger_typing()

        music_player = self.bot.guild_players.get(ctx.guild.id)

        # if just play entered, resumes paused song or starts the currently queued songs
        if url is None:
            if music_player is not None:
                await self.resume(ctx)
                music_player.start_player = True
        else:
            if music_player is None:
                self.bot.guild_players[ctx.guild.id] = MusicPlayer(ctx, self.bot)
                music_player = self.bot.guild_players.get(ctx.guild.id)
            else:
                music_player.set_context(ctx)

            await self.add_queue(url, music_player)

    async def add_queue(self, url, music_player):
        tracks = self.get_spotify(url)

        music_player.track_list += tracks
        # print(self.bot.music_player.track_list)

        if len(tracks) > 0:
            for track in tracks:
                if len(tracks) > 1:
                    await music_player.add_track(track + " audio", False)
                else:
                    await music_player.add_track(track + " audio", True)
        else:
            await music_player.add_track(url, True)

    def get_spotify(self, url):
        tracks = []

        if "https://open.spotify.com/playlist/" in url:
            url_id = url.removesuffix("https://open.spotify.com/playlist/")
            url_id = url_id.split("?")
            sp_id = url_id[0]

            sp = SpotifyClient()
            # sort by date added, else custom order
            if "-added" in url:
                playlist = sp.get_playlist(sp_id, True)
            else:
                playlist = sp.get_playlist(sp_id)

            for track in playlist:
                tracks.append(track)

        if "https://open.spotify.com/track/" in url:
            url_id = url.removesuffix("https://open.spotify.com/track/")
            url_id = url_id.split("?")
            sp_id = url_id[0]

            sp = SpotifyClient()
            track = sp.get_track(sp_id)
            tracks.append(track)

        return tracks

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                print_log(f"Joining channel {ctx.author.voice.channel}")
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        else:
            if (
                ctx.author.voice
                and ctx.author.voice.channel != ctx.voice_client.channel
            ):
                self.bot.music_player.clear_queue()
                await ctx.voice_client.disconnect()
                print_log(f"Joining channel {ctx.author.voice.channel}")
                await ctx.author.voice.channel.connect()
                print_log(f"Joined channel {ctx.author.voice.channel}")
                self.bot.music_player.set_context(ctx)

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @commands.command()
    async def pause(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send(
                "I am not currently playing anything!", delete_after=20
            )
        elif ctx.voice_client.is_paused():
            return

        ctx.voice_client.pause()
        await ctx.send("Paused current song")

    async def resume(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send(
                "I am not currently playing anything!", delete_after=20
            )
        elif not ctx.voice_client.is_paused():
            return

        ctx.voice_client.resume()
        await ctx.send("Resumed the song!")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client.is_playing():
            self.bot.music_play.is_loop = False
            ctx.voice_client.stop()
        else:
            return await ctx.send(
                "I am not currently playing anything!", delete_after=20
            )

    @commands.command(name="loop", aliases=["l", 'repeat'])
    async def loop(self, ctx):
        if ctx.voice_client.is_playing():
            self.bot.music_player.is_loop = not self.bot.music_player.is_loop
        else:
            return await ctx.send(
                "I am not currently playing anything!", delete_after=20
            )

    @commands.command()
    async def test(self, ctx):
        array = ['blue notes meek mill', '1 step forward 2 steps back', 'chronomentrophoba', 'funkin around outcast', 'liberation with cee lo']
        queue = MusicQueue(ctx)
        queue.track_list = array
        print(queue.track_list)
        await queue.load()

def setup(bot):
    bot.add_cog(Music(bot))
