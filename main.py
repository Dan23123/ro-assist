import discord
import time

from discord.ext import tasks, commands
from database import get_guild
from config import BOT_TOKEN, YOUTUBE_TOKEN, BOT_VERSION

COGS_LIST = [
	"cogs.info",
	"cogs.roblox",
	"cogs.economy",
	"cogs.giveaways",
	"cogs.youtube",
	"cogs.moderation",
	"cogs.fun"
]

async def get_prefix(bot, message):
	return commands.when_mentioned_or(get_guild(message.guild.id)[1])(bot, message)

"""
intents = discord.Intents.default()
intents.members = True
"""
client = commands.Bot(
	command_prefix = get_prefix
)

@client.event
async def on_ready():
	for cog in COGS_LIST:
		client.load_extension(cog)

	print("[CLIENT] Bot is ready.")
	print(f"[CLIENT] Using discord.py {discord.__version__}.")
	print(f"[CLIENT] Bot's version: {BOT_VERSION}.")

if __name__ == '__main__':
	client.run(BOT_TOKEN)