import discord
import aiohttp
import html

from discord.ext import commands
from random import randint, choice
from database import db, cursor, get_guild

REDDITS = ["dankmemes", "memes"]

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    @commands.command(
        name = "how-cool",
        description = "Shows how cool user is",
        usage = "[user]"
    )
    async def howcool(self, ctx, member: discord.Member):
        progress = randint(0, 100)
        await ctx.send(embed = discord.Embed(title = "How Cool", description = f"{member.mention} is {progress}% cool.", colour = discord.Colour.from_hsv(progress / 255, 1, 1)))

    @commands.command(
        name = "how-gay",
        description = "You know what it does",
        usage = "[user]"
    )
    async def howgay(self, ctx, member: discord.Member):
        progress = randint(0, 100)
        await ctx.send(embed = discord.Embed(title = "How Gay", description = f"{member.mention} is {progress}% gay.", colour = discord.Colour.from_hsv(progress / 255, 1, 1)))

    @commands.command(
        name = "iq-test",
        description = "Shows user's IQ",
        usage = "[user]"
    )
    async def iqtest(self, ctx, member: discord.Member):
        iq = randint(0, 160)
        await ctx.send(embed = discord.Embed(title = "IQ Test", description =f"{member.mention}'s IQ is {iq}.", colour = discord.Colour.blurple()))

    @commands.command(
        description = "Sends random meme from reddit"
    )
    async def meme(self, ctx):
        random_reddit = choice(REDDITS)

        async with self.session.get(f"https://www.reddit.com/r/{random_reddit}/new.json?sort=hot") as r:
            result = await r.json()
            random_post = randint(0, 24)

            embed = discord.Embed(title = result["data"]["children"][random_post]["data"]["title"], colour = discord.Colour.green())
            embed.set_image(url = result["data"]["children"][random_post]["data"]["url"])

            await ctx.send(embed = embed)

    @commands.command(
        name = "heads-or-tails",
        description = "Heads or Tails game"
    )
    async def headsortails(self, ctx):
        if randint(0, 1) == 0:
            await ctx.send(f"{ctx.author.mention}, heads!")
        else:
            await ctx.send(f"{ctx.author.mention}, tails!")

    @commands.command(
        description = "Sends embed with your text",
        usage = "[text]"
    )
    async def embed(self, ctx, *, text):
        await ctx.message.delete()

        webhooks = await ctx.channel.webhooks()
        webhook = discord.utils.get(webhooks, user = self.bot.user)

        if webhook == None:
            webhook = await ctx.channel.create_webhook(name = "RoHelpWebhook")

        await webhook.send(embed = discord.Embed(description = text, colour = discord.Colour.green()), username = ctx.author.display_name, avatar_url = str(ctx.author.avatar_url))

    @commands.command(
        description = "Gets avatar of user",
        usage = "[user]"
    )
    async def avatar(self, ctx, member: discord.Member):
        embed = discord.Embed(title = str(member), colour = discord.Colour.green())
        embed.set_image(url = str(member.avatar_url))

        await ctx.send(embed = embed)

    @commands.command(
        name = "set-suggestion-channel",
        description = "Sets suggestion channel"
    )
    @commands.has_permissions(manage_channels = True)
    async def set_suggestion_channel(self, ctx):
        cursor.execute("UPDATE guilds SET suggestion_channel_id = %s WHERE guild_id = %s", (ctx.channel.id, ctx.guild.id,))
        db.commit()

        embed_success = discord.Embed(title = "Suggestion", description = f"Set {ctx.channel.mention} channel as suggestion channel. :white_check_mark:", colour = discord.Colour.green())
        embed_success.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

        await ctx.send(embed = embed_success)

    @commands.command(
        name = "remove-suggestion-channel",
        description = "Removes suggestion channel"
    )
    @commands.has_permissions(manage_channels = True)
    async def remove_suggestion_channel(self, ctx):
        if get_guild(ctx.guild.id)[6] == None:
            embed_failure = discord.Embed(title = "Suggestion", description = f"You don't have suggestion channel. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        cursor.execute("UPDATE guilds SET suggestion_channel_id = %s WHERE guild_id = %s", (None, ctx.guild.id))
        db.commit()

        embed_success = discord.Embed(title = "Suggestion", description = f"Removed suggestion channel. :white_check_mark:", colour = discord.Colour.green())
        embed_success.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

        await ctx.send(embed = embed_success)

    @commands.command(
        description = "Makes suggestion",
        usage = "[suggestion]"
    )
    async def suggestion(self, ctx, *, suggestion):
        suggestion_channel_id = get_guild(ctx.guild.id)[6]
        channel = ctx.guild.get_channel(suggestion_channel_id)

        if channel == None:
            embed_failure = discord.Embed(title = "Suggestion", description = f"I couldn't find suggestion channel. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        embed_suggestion = discord.Embed(title = "Suggestion", description = suggestion, colour = discord.Colour.green())
        embed_suggestion.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

        message = await channel.send(embed = embed_suggestion)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        embed_success = discord.Embed(title = "Suggestion", description = f"Sent your suggestion to suggestions channel ({channel.mention}). :white_check_mark:", colour = discord.Colour.green())
        embed_success.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

        await ctx.send(embed = embed_success)

def setup(bot):
    bot.add_cog(Fun(bot))