import discord
import re

from discord.ext import commands
from database import db, cursor, get_user, get_guild

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = get_guild(channel.guild.id)

        if guild[5] != None:
            role = channel.guild.get_role(guild[5])
            if role != None:
                await channel.set_permissions(role, send_messages = False)
            else:
                cursor.execute("UPDATE guilds SET muted_role_id = ? WHERE guild_id = ?", (None, channel.guild.id,))
                db.commit()

    @commands.command(
        description = "Kicks specific member",
        usage = "[target] [reason (optional)]"
    )
    @commands.has_permissions(kick_members = True)
    async def kick(self, ctx, target: discord.Member, *, reason = None):
        if ctx.author == target:
            embed_failure = discord.Embed(title = "Kick", description = "You can't kick yourself. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        if ctx.author != ctx.guild.owner and (target == ctx.guild.owner or ctx.author.top_role <= target.top_role):
            embed_failure = discord.Embed(title = "Kick", description = "You can't kick that user. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        await target.kick(reason = reason)
        await ctx.send(embed = discord.Embed(title = "Kick", description = f"{target.mention} has been kicked by {ctx.author.mention}. Reason: {reason}", colour = discord.Colour.green()))

    @kick.error
    async def kickerror(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
            embed_failure = discord.Embed(title = "Kick", description = "You can't kick that user. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            await ctx.send(embed = embed_failure)

    @commands.command(
        description = "Bans specific member",
        usage = "[target] [reason (optional)]"
    )
    @commands.has_permissions(ban_members = True)
    async def ban(self, ctx, target: discord.Member, *, reason = None):
        if ctx.author == target:
            embed_failure = discord.Embed(title = "Ban", description = "You can't ban yourself. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        if ctx.author != ctx.guild.owner and (target == ctx.guild.owner or ctx.author.top_role <= target.top_role):
            embed_failure = discord.Embed(title = "Ban", description = "You can't kick ban user. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        await target.ban(reason = reason)
        await ctx.send(embed = discord.Embed(title = "Ban", description = f"{target.mention} has been banned by {ctx.author.mention}. Reason: {reason}", colour = discord.Colour.green()))

    @ban.error
    async def banerror(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
            embed_failure = discord.Embed(title = "Ban", description = "You can't ban that user. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            await ctx.send(embed = embed_failure)

    @commands.command(
        description = "Unbans a user from the server",
        usage = "[target_id] [reason (optional)]"
    )
    @commands.has_permissions(ban_members = True)
    async def unban(self, ctx, user_id: int, *, reason = None):
        ban_entries = await ctx.guild.bans()

        for ban_entry in ban_entries:
            if ban_entry.user.id == user_id:
                await ctx.guild.unban(ban_entry.user, reason = reason)
                await ctx.send(embed = discord.Embed(title = "Unban", description = f"{ban_entry.user} has been unbanned by {ctx.author.mention}. Reason: {reason}", colour = discord.Colour.green()))

                return

        embed_failure = discord.Embed(title = "Unban", description = "User not found. :x:", colour = discord.Colour.red())
        embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

        await ctx.send(embed = embed_failure)

    @unban.error
    async def unbanerror(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
            embed_failure = discord.Embed(title = "Unban", description = "You can't unban that user. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            await ctx.send(embed = embed_failure)

    @commands.command(
        description = "Delete a channel's messages",
        usage = "[limit (default = 1)]"
    )
    @commands.has_permissions(manage_channels = True)
    async def clear(self, ctx, limit = 1):
        await ctx.message.delete()

        deleted = await ctx.channel.purge(limit = limit)
        await ctx.send(embed = discord.Embed(title = "Clear", description = f"Deleted {len(deleted)} messages. :white_check_mark:", colour = discord.Colour.green()), delete_after = 5.0)

    @commands.command(
        description = "Server-mutes a user",
        usage = "[target] [reason (optional)]"
    )
    @commands.has_permissions(mute_members = True)
    async def mute(self, ctx, target: discord.Member, *, reason = None):
        if ctx.author == target:
            embed_failure = discord.Embed(title = "Mute", description = "You can't mute yourself. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        if ctx.author != ctx.guild.owner and (target == ctx.guild.owner or ctx.author.top_role <= target.top_role):
            embed_failure = discord.Embed(title = "Mute", description = "You can't mute that user. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        guild = get_guild(ctx.guild.id)
        role = None

        if guild[5] == None or ctx.guild.get_role(guild[5]) == None:
            role = await ctx.guild.create_role(name = "Muted", permissions = discord.Permissions(0))

            for channel in ctx.guild.text_channels:
                await channel.set_permissions(role, send_messages = False)

            cursor.execute("UPDATE guilds SET muted_role_id = ? WHERE guild_id = ?", (role.id, ctx.guild.id))
            db.commit()
        else:
            role = ctx.guild.get_role(guild[5])

        if role not in target.roles:
            await target.add_roles(role)
            await ctx.send(embed = discord.Embed(title = "Mute", description = f"{target.mention} has been muted by {ctx.author.mention}. Reason: {reason}", colour = discord.Colour.green()))
        else:
            embed_failure = discord.Embed(title = "Mute", description = "You can't mute that user. He is already muted. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            await ctx.send(embed = embed_failure)

    @mute.error
    async def muteerror(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
            embed_failure = discord.Embed(title = "Mute", description = "You can't mute that user. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            await ctx.send(embed = embed_failure)

    @commands.command(
        description = "Unmutes a user",
        usage = "[target] [reason (optional)]"
    )
    @commands.has_permissions(mute_members = True)
    async def unmute(self, ctx, target: discord.Member, *, reason = None):
        guild = get_guild(ctx.guild.id)

        if guild[5] != None and ctx.guild.get_role(guild[5]) != None:
            await target.remove_roles(ctx.guild.get_role(guild[5]))
            await ctx.send(embed = discord.Embed(title = "Unmute", description = f"{target.mention} has been unmuted by {ctx.author.mention}. Reason: {reason}", colour = discord.Colour.green()))
        else:
            embed_failure = discord.Embed(title = "Unmute", description = "You can't unmute that user. He is not muted. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            await ctx.send(embed = embed_failure)

    @unmute.error
    async def unmuteerror(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
            embed_failure = discord.Embed(title = "Unmute", description = "You can't unmute that user. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            await ctx.send(embed = embed_failure)

    @commands.command(
        name = "user-info",
        description = "Get information about the user",
        usage = "[target]"
    )
    async def userinfo(self, ctx, target: discord.Member):
        embed_user_info = discord.Embed(title = "Server Info", colour = discord.Colour.green())

        embed_user_info.add_field(name = "User Name", value = str(ctx.author))
        embed_user_info.add_field(name = "User ID", value = ctx.author.id)
        embed_user_info.add_field(name = "Top Role", value = ctx.author.top_role.mention)

        await ctx.send(embed = embed_user_info)

    @commands.command(
        name = "server-info",
        description = "Get information about the server"
    )
    async def serverinfo(self, ctx):
        embed_server_info = discord.Embed(title = "Server Info", colour = discord.Colour.green())

        embed_server_info.add_field(name = "Server Name", value = ctx.guild.name)
        embed_server_info.add_field(name = "Server ID", value = ctx.guild.id)
        embed_server_info.add_field(name = "Server Owner", value = ctx.guild.owner.mention)
        embed_server_info.add_field(name = "Members", value = len(ctx.guild.members))
        embed_server_info.add_field(name = "Text Channels", value = len(ctx.guild.text_channels))
        embed_server_info.add_field(name = "Voice Channels", value = len(ctx.guild.voice_channels))
        embed_server_info.add_field(name = "Emoji Limit", value = ctx.guild.emoji_limit)

        await ctx.send(embed = embed_server_info)

    @commands.command(
        description = "Nukes channel"
    )
    @commands.has_permissions(manage_channels = True)
    async def nuke(self, ctx):
        name = ctx.channel.name
        overwrites = ctx.channel.overwrites
        category = ctx.channel.category
        position = ctx.channel.position
        topic = ctx.channel.topic
        slowmode_delay = ctx.channel.slowmode_delay
        nsfw = ctx.channel.nsfw

        await ctx.channel.delete()
        channel = await ctx.guild.create_text_channel(name, overwrites = overwrites, category = category, topic = topic, slowmode_delay = slowmode_delay, nsfw = nsfw, position = position)
        await channel.send(":white_check_mark: Nuked this channel.\nhttps://tenor.com/view/explosion-explode-clouds-of-smoke-gif-17216934")

def setup(bot):
    bot.add_cog(Moderation(bot))