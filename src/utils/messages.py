import discord

NOT_CONNECTED_USER = "You are not connected to a voice channel"
NOT_CONNECTED_BOT = "I am not currently connected to voice!"
NOT_PLAYING = "I am not currently playing anything!"
EMPTY_QUEUE = "There are currently no more queued songs"

def send_message(ctx: discord.ext.commands.Context, message:str):
  ctx.send(message)

async def trigger_typing(ctx: discord.ext.commands.Context):
  await ctx.trigger_typing()
