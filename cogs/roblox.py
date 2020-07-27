import discord
import aiohttp

from discord.ext import commands
from bs4 import BeautifulSoup
from database import db, cursor, get_guild
from random import randint

WORDS = ["and", "or", "hi", "cheese", "apple", "roblox", "bye", "orange", "banana", "nice"]

class Roblox(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		guild = get_guild(channel.guild.id)
		if channel.id == guild[2]:
			cursor.execute("UPDATE guilds SET verification_channel_id = ?, verification_role_id = ?, verification_set_username = ? WHERE guild_id = ?", (None, None, None, channel.guild.id))
			db.commit()

	@commands.command(
		name = "roblox-user",
		description = "Get specific ROBLOX user's information",
		usage = "[username]"
	)
	async def robloxuser(self, ctx, username):
		embed = discord.Embed(title = "ROBLOX User", description = "Collecting data...", colour = discord.Colour.gold())
		embed.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))
		await ctx.send(embed = embed)

		user = await self.get_user(username)
		if user != None:
			embed_user_data = discord.Embed(title = username, colour = discord.Colour.green())
			embed_user_data.set_thumbnail(url = user["AvatarUrl"])

			embed_user_data.add_field(name = "Username", value = user["Username"])
			embed_user_data.add_field(name = "User ID", value = user["Id"])
			embed_user_data.add_field(name = "Is online", value = ("Yes" if user["IsOnline"] else "No"))
			embed_user_data.add_field(name = "Friends", value = user["FriendshipCount"])
			embed_user_data.add_field(name = "Followers", value = user["FollowersCount"])
			embed_user_data.add_field(name = "Followings", value = user["FollowingsCount"])
			embed_user_data.add_field(name = "Groups", value = user["GroupsCount"])

			await ctx.send(embed = embed_user_data)
		else:
			embed = discord.Embed(title = "Get specific user's ROBLOX information", description = "User not found. :x:", colour = discord.Colour.red())
			embed.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

			await ctx.send(embed = embed)

	@commands.command(
		name = "setup-verify",
		description = "Set up ROBLOX verification system for your server"
	)
	@commands.has_permissions(manage_channels = True, manage_roles = True, manage_nicknames = True)
	async def setupverify(self, ctx):
		check = lambda message: message.channel == ctx.channel and message.author == ctx.author

		await ctx.send(embed = discord.Embed(title = "Verification Setup", description = "Step 1: choose which role you want to give after completing verification (you can skip this step by saying \"skip\").\n(30 seconds to answer)", colour = discord.Colour.blurple()))
		msg1 = await self.bot.wait_for("message", timeout = 30.0, check = check)
		verification_role = None

		if msg1.content != "skip":
			try:
				role = await commands.RoleConverter().convert(ctx, msg1.content)
				verification_role = role.id
			except:
				return await ctx.send(embed = discord.Embed(title = "Verification Setup", description = "Failed to set up verification: invalid role. :x:", colour = discord.Colour.red()))

		msg2 = await ctx.send(embed = discord.Embed(title = "Verification Setup", description = "Step 2: do you want to set user's nickname as their roblox username?\n(30 seconds to answer)", colour = discord.Colour.blurple()))
		await msg2.add_reaction("☑️")
		await msg2.add_reaction("❌")

		reaction, user = await self.bot.wait_for("reaction_add", timeout = 30.0, check = lambda reaction, user: reaction.message.id == msg2.id and user.id == ctx.author.id)
		verification_set_username = None

		if reaction.emoji == "☑️":
			verification_set_username = True
		elif reaction.emoji == "❌":
			verification_set_username = False
		else:
			return await ctx.send(embed = discord.Embed(title = "Verification Setup", description = "Failed to set up verification: invalid answer. :x:", colour = discord.Colour.red()))

		cursor.execute("UPDATE guilds SET verification_channel_id = ?, verification_role_id = ?, verification_set_username = ? WHERE guild_id = ?", (ctx.channel.id, verification_role, verification_set_username, ctx.guild.id,))
		db.commit()

		await ctx.send(embed = discord.Embed(title = "Verification Setup", description = f"Set up verification for {ctx.channel.mention} channel. :white_check_mark:", colour = discord.Colour.green()))

	@commands.command(
		description = "Complete verification using this command"
	)
	async def verify(self, ctx):
		guild = get_guild(ctx.guild.id)

		if ctx.channel.id == guild[2]:
			check = lambda message: message.channel == ctx.channel and message.author == ctx.author

			embed_step1 = discord.Embed(title = "Verification", description = "Step 1: tell your ROBLOX username.\n(30 seconds to answer)", colour = discord.Colour.blurple())
			embed_step1.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))
		
			await ctx.send(embed = embed_step1)
			message1 = await self.bot.wait_for("message", timeout = 30.0, check = check)
			user = await self.get_user(message1.content)

			if user == None:
				embed_failure = discord.Embed(title = "Verification", description = "Failed to verify: invalid user. :x:", colour = discord.Colour.red())
				embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

				return await ctx.send(embed = embed_failure)

			status = self.generate_status()
			embed_step2 = discord.Embed(title = "Verification", description = f"Step 2: set your \"About\" section to \"{status}\". After this say \"verify-end\".\n(3 minutes to answer)", colour = discord.Colour.blurple())
			embed_step2.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

			await ctx.send(embed = embed_step2)
			await self.bot.wait_for("message", timeout = 180.0, check = lambda message: message.channel == ctx.channel and message.author == ctx.author and message.content == "verify-end")

			embed_check = discord.Embed(title = "", description = "Checking \"About\" section...", colour = discord.Colour.gold())
			embed_check.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

			await ctx.send(embed = embed_check)

			async with aiohttp.ClientSession() as session:
				async with session.get(f"https://www.roblox.com/users/{user['Id']}/profile") as r:
					text = await r.text()
					soup = BeautifulSoup(text, "lxml")
					status_object = soup.find("span", class_="profile-about-content-text linkify")

					if status_object == None or status_object.text != status:
						embed_failure = discord.Embed(title = "Verification", description = "Failed to verify: invalid \"About\" section. :x:", colour = discord.Colour.red())
						embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

						return await ctx.send(embed = embed_failure)

					if guild[3] != None:
						role = discord.utils.get(ctx.guild.roles, id = guild[3])
						if role != None:
							await ctx.author.add_roles(role)
						else:
							cursor.execute("UPDATE guilds SET verification_role_id = ? WHERE guild_id = ?", (None, ctx.guild.id))
							db.commit()

					if guild[4] == 1:
						try:
							await ctx.author.edit(nick = user["Username"])
						except:
							pass

					cursor.execute("UPDATE users SET roblox_id = ? WHERE user_id = ?", (user["Id"], ctx.author.id))
					db.commit()

					embed_success = discord.Embed(title = "Verification", description = "Verification completed. :white_check_mark:", colour = discord.Colour.green())
					embed_success.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

					await ctx.send(embed = embed_success)

	def generate_status(self):
		words = []

		for i in range(12):
			words.append(WORDS[randint(0, len(WORDS) - 1)])

		return " ".join(words)

	async def get_user(self, username):
		async with aiohttp.ClientSession() as session:
			async with session.get(f"https://api.roblox.com/users/get-by-username?username={username}") as r:
				result = await r.json()
				if "Id" in result:
					async with session.get(f"https://friends.roblox.com/v1/users/{result['Id']}/friends/count") as r:
						data = await r.json()
						result["FriendshipCount"] = data["count"]

					async with session.get(f"https://api.roblox.com/users/{result['Id']}/groups") as r:
						data = await r.json()
						result["GroupsCount"] = len(data)

					async with session.get(f"https://friends.roblox.com/v1/users/{result['Id']}/followers/count") as r:
						data = await r.json()
						result["FollowersCount"] = data["count"]

					async with session.get(f"https://friends.roblox.com/v1/users/{result['Id']}/followings/count") as r:
						data = await r.json()
						result["FollowingsCount"] = data["count"]

					async with session.get(f"https://www.roblox.com/Thumbs/Avatar.ashx?x=100&y=100&userId={result['Id']}") as r:
						result["AvatarUrl"] = r.url.human_repr()

					async with session.get(f"https://groups.roblox.com/v2/users/{result['Id']}/groups/roles") as r:
						data = await r.json()
						result["Groups"] = data["data"]

					return result

def setup(bot):
	bot.add_cog(Roblox(bot))