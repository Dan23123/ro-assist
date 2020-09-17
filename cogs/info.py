import discord
import aiohttp
import os
import psutil
import sys
import time

from discord.ext import commands, tasks
from database import db, cursor, get_guild, get_all_guilds, get_all_giveaways, get_all_users, delete_user
from math import ceil
from random import randint
from config import BOT_VERSION, DISCORD_BOTS_TOKEN, DISCORD_BOT_LIST_TOKEN

COMMANDS_PER_PAGE = 9
IGNORE_COMMANDS = ["add-stat", "set-stat"]

class Info(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.bot.remove_command("help")
		self.data_update.start()
		self.autocleaner.start()

	@tasks.loop(seconds = 15.0)
	async def data_update(self):
		activity = ""
		choice = randint(0, 2)

		if choice == 0:
			activity = f"{len(self.bot.users)} members"
		elif choice == 1:
			activity = f"{len(self.bot.commands)} commands"
		else:
			activity = f"{len(self.bot.guilds)} servers"

		await self.bot.change_presence(
			activity = discord.Activity(name = activity, type = discord.ActivityType.watching),
			status = discord.Status.dnd
		)

		async with aiohttp.ClientSession() as session:
			headers1 = {
				"Authorization": DISCORD_BOTS_TOKEN
			}
			headers2 = {
				"Authorization": DISCORD_BOT_LIST_TOKEN
			}

			data1 = {
				"guildCount": len(self.bot.guilds)
			}
			data2 = {
				"guilds": len(self.bot.guilds),
				"users": len(self.bot.users)
			}

			async with session.post(f"https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats", data = data1, headers = headers1) as r:
				pass
			async with session.post(f"https://discordbotlist.com/api/v1/bots{self.bot.user.id}/stats", data = data2, headers = headers2) as r:
				pass

	@tasks.loop(minutes = 1.0)
	async def autocleaner(self):
		for guild in get_all_guilds():
			if self.bot.get_guild(guild[0]) == None:
				delete_guild(guild[0])

		for gw in get_all_giveaways():
			if time.time() >= (gw[6] + 86400):
				delete_giveaway(gw[0], gw[1], gw[2])

		for user in get_all_users():
			if self.bot.get_user(user[0]) == None:
				delete_user(user[0])

	@commands.Cog.listener()
	async def on_error(self, event, *args, **kwargs):
		print(f"[CLIENT] Exception raised by {event} event: {sys.exc_info()}")

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		print(f"[CLIENT] Exception raised by command: {error}")

		if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
			embed = discord.Embed(title = "Command Error", description = f"Use: !{ctx.command.name} {ctx.command.usage if ctx.command.usage is not None else ''}", colour = discord.Colour.red())
			embed.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

			await ctx.send(embed = embed)
		elif isinstance(error, commands.CheckFailure):
			embed = discord.Embed(title = "Command Error", description = f"You are lacking permissions to use this command. :x:", colour = discord.Colour.red())
			embed.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

			await ctx.send(embed = embed)
		elif isinstance(error, commands.CommandOnCooldown):
			embed = discord.Embed(title = "Command Error", description = f"You can use this command {error.cooldown.rate} time every {time.strftime('%M', time.gmtime(error.cooldown.per))} minutes. Retry after {time.strftime('%M', time.gmtime(error.retry_after))} minutes. :x:", colour = discord.Colour.red())
			embed.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

			await ctx.send(embed = embed)

	@commands.command(
		description = "Shows help message"
	)
	async def help(self, ctx, section = None, page: int = 1):
		embed_help = discord.Embed(title = "Help", colour = discord.Colour.green())

		if section == None:
			embed_help.description = "Use: !help [section] [page (optional)]"

			for cog in self.bot.cogs:
				cog_name = (cog.qualified_name if isinstance(cog, commands.Cog) else cog)
				embed_help.add_field(name = f"```help {cog_name.lower()}```", value = f"{cog_name} Section")
		else:
			cog = self.bot.get_cog(section.title())

			if cog == None:
				embed_failure = discord.Embed(title = "Help", description = "Invalid section. :x:", colour = discord.Colour.red())
				embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

				return await ctx.send(embed = embed_failure)

			cmds = cog.get_commands()
			ln = len(cmds)
			pages = ceil(ln / COMMANDS_PER_PAGE)

			if page < 1 or page > pages:
				embed_failure = discord.Embed(title = "Help", description = "Invalid page. :x:", colour = discord.Colour.red())
				embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

				return await ctx.send(embed = embed_failure)

			embed_help.set_footer(text = f"Page: {page} / {pages}")

			r1 = (COMMANDS_PER_PAGE * (page - 1))
			r2 = ((COMMANDS_PER_PAGE * page) if (COMMANDS_PER_PAGE * page) <= ln else ln)

			for i in range(r1, r2):
				if cmds[i].name not in IGNORE_COMMANDS:
					embed_help.add_field(name = f"`!{cmds[i].name} {cmds[i].usage if cmds[i].usage != None else ''}`", value = (cmds[i].description if len(cmds[i].description) > 0 else "Description not provided"), inline = False)

		await ctx.send(embed = embed_help)

	@commands.command(
		name = "invite-link",
		description = "Get invite link for the bot",
		aliases = ["invite"]
	)
	async def invitelink(self, ctx):
		await ctx.send(embed = discord.Embed(title = "Bot's invite link", description = "Invite link: https://discord.com/api/oauth2/authorize?client_id=711580413771907072&permissions=8&scope=bot", colour = discord.Colour.green()))

	@commands.command(
		name = "bot-info",
		description = "Gets information about the bot"
	)
	async def info_bot(self, ctx):
		embed_info = discord.Embed(name = "Bot's Info", description = f"Using discord.py {discord.__version__}", colour = discord.Colour.green())

		embed_info.add_field(name = "Ping", value = f"{round(self.bot.latency * 1000)}ms", inline = False)
		embed_info.add_field(name = "Memory Usage", value = f"{round(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2)}MB / {round(psutil.virtual_memory().total / 1024 ** 2)}MB", inline = False)
		embed_info.add_field(name = "Bot's Version", value = BOT_VERSION, inline = False)
		embed_info.add_field(name = "Servers", value = len(self.bot.guilds), inline = False)
		embed_info.add_field(name = "Users", value = len(self.bot.users), inline = False)

		await ctx.send(embed = embed_info)

	@commands.command(
		name = "set-prefix",
		description = "Set new bot's prefix for this server"
	)
	@commands.has_permissions(manage_messages = True)
	async def set_prefix(self, ctx, prefix):
		if len(prefix) == 1:
			cursor.execute("UPDATE guilds SET prefix = %s WHERE guild_id = %s", (prefix, ctx.guild.id,))
			db.commit()

			await ctx.send(embed = discord.Embed(title = "Set Prefix", description = f"My new prefix for this server is \"{prefix}\". :white_check_mark:", colour = discord.Colour.green()))
		else:
			await ctx.send(embed = discord.Embed(title = "Set Prefix", description = "Prefix length must be exactly 1 character. :x:", colour = discord.Colour.red()))

	@commands.command(
		name = "prefix",
		description = "Get bot's prefix for current server"
	)
	async def get_prefix(self, ctx):
		await ctx.send(embed = discord.Embed(title = "Bot's Prefix", description = f"My prefix on this server is \"{get_guild(ctx.guild.id)[1]}\".", colour = discord.Colour.green()))

	@commands.command(
		description = "If you found a glitch, you can report it by using this command",
		usage = "[description]"
	)
	@commands.cooldown(1, 120, commands.BucketType.user)
	async def report(self, ctx, *, description):
		guild = self.bot.get_guild(707582068112097300)
		channel = guild.get_channel(736935317738750022)

		await channel.send(embed = discord.Embed(title = f"Glitch report from {ctx.author}", description = description, colour = discord.Colour.green()))
		embed_success = discord.Embed(title = "Glitch Report", description = f"Thank you for reporting glitch!", colour = discord.Colour.green())
		embed_success.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

		await ctx.send(embed = embed_success)

def setup(bot):
	bot.add_cog(Info(bot))