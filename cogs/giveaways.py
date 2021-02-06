import discord
import time
import aiohttp

from discord.ext import commands, tasks
from converters import TimeConverter
from database import db, cursor, add_giveaway, delete_giveaway, get_giveaway, get_all_giveaways, get_guild_giveaways, get_user
from random import choice
from math import ceil

MUST_JOIN_DISCORD_SERVER = 1
MUST_JOIN_ROBLOX_GROUP = 2
MAX_REQUIREMENTS = 5
GIVEAWAYS_PER_PAGE = 9

class Requirement:
    def __init__(self, type_, data):
        self.type = type_
        self.data = data

    def __repr__(self):
        return f"({self.type}:{self.data})"

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaway_loop.start()

    @commands.command(
        name = "start-giveaway",
        description = "Starts giveaway"
    )
    @commands.has_permissions(manage_channels = True, manage_messages = True)
    async def start_giveaway(self, ctx):
        check = lambda message: message.author == ctx.author and message.channel == ctx.channel

        await ctx.send("Alright, let's get started. In which channel do you want to start the giveaway?")
        msg1 = await self.bot.wait_for("message", timeout = 30.0, check = check)

        try:
            channel = await commands.TextChannelConverter().convert(ctx, msg1.content)
        except commands.ChannelNotFound:
            return await ctx.send("Invalid channel. :x:")

        await ctx.send("Alright, let's get started. What do you want to giveaway?")
        msg2 = await self.bot.wait_for("message", timeout = 30.0, check = check)
        reward = msg1.content

        await ctx.send("How many winners?")
        msg3 = await self.bot.wait_for("message", timeout = 30.0, check = check)

        try:
            winners = int(msg3.content)
        except ValueError:
            return await ctx.send("Invalid winners amount. :x:")

        if winners < 1 or winners > 10:
            return await ctx.send("Invalid winners amount (1-10). :x:")

        await ctx.send("How long it will be? For example: 2s, 3h, 4d.")
        msg4 = await self.bot.wait_for("message", timeout = 30.0, check = check)

        giveaway_time = await TimeConverter().convert(ctx, msg4.content)
        if giveaway_time == None or giveaway_time > 1728000:
            return await ctx.send("Invalid giveaway time (1s-20d). :x:")

        requirements = []

        while True:
            if len(requirements) >= MAX_REQUIREMENTS:
                return await ctx.send("Limit of requirements reached.")

            await ctx.send("You can setup some requirements. Here's the list:\n- must-join-roblox-group\n\n(say \"skip\" to skip this step)")
            msg = await self.bot.wait_for("message", timeout = 30.0, check = check)

            if msg.content == "must-join-roblox-group":
                await ctx.send("Send ROBLOX group ID.")
                msg = await self.bot.wait_for("message", timeout = 30.0, check = check)

                try:
                    roblox_group_id = int(msg.content)
                    requirements.append(Requirement(MUST_JOIN_ROBLOX_GROUP, roblox_group_id))

                    await ctx.send("Added ROBLOX group to requirements. :white_check_mark:")
                except ValueError:
                    await ctx.send("Invalid ROBLOX group ID. :x:")

            if msg.content == "skip":
                break

        giveaway_time += time.time()
        time_string = time.strftime("on %m/%d/%Y at %H:%M:%S", time.gmtime(giveaway_time))

        requirement_texts = [repr(req) for req in requirements]
        db_requirements = ",".join(requirement_texts)
        requirement_text = ""

        r1 = discord.utils.get(requirements, type = MUST_JOIN_ROBLOX_GROUP)
        if r1 != None:
            requirement_text += "Must join ROBLOX groups:\n"

            for requirement in requirements:
                if requirement.type == MUST_JOIN_ROBLOX_GROUP:
                    requirement_text += f"https://www.roblox.com/groups/{requirement.data}/group\n"

        embed_giveaway = discord.Embed(title = "Giveaway", description = f"""
        Reward: **{reward}**
        Winners: **{winners}**
        Ends **{time_string}**

        {requirement_text}
        """, colour = discord.Colour.blurple())

        giveaway_message = await ctx.send("React with :tada: to enter the giveaway.", embed = embed_giveaway)
        await giveaway_message.add_reaction("🎉")

        add_giveaway(ctx.guild.id, ctx.channel.id, giveaway_message.id, reward, winners, db_requirements, giveaway_time)

    @commands.command(
        name = "start-giveaway-short",
        description = "Starts giveaway (short command)",
        usage = "[winners] [giveaway_time] [reward]"
    )
    @commands.has_permissions(manage_channels = True, manage_messages = True)
    async def start_giveaway_short(self, ctx, winners: int, giveaway_time, *, reward):
        giveaway_time = await TimeConverter().convert(ctx, giveaway_time)
        if giveaway_time == None or giveaway_time > 1728000:
            return await ctx.send("Invalid giveaway time (1s-20d). :x:")

        giveaway_time += time.time()
        time_string = time.strftime("on %m/%d/%Y at %H:%M:%S", time.gmtime(giveaway_time))

        embed_giveaway = discord.Embed(title = "Giveaway", description = f"""
Reward: **{reward}**
Winners: **{winners}**
Ends **{time_string}**
        """, colour = discord.Colour.blurple())

        giveaway_message = await ctx.send("React with :tada: to enter the giveaway.", embed = embed_giveaway)
        await giveaway_message.add_reaction("🎉")

        add_giveaway(ctx.guild.id, ctx.channel.id, giveaway_message.id, reward, winners, "", giveaway_time)

    @commands.command(
        name = "reroll-giveaway",
        description = "Picks new winner of the giveaway",
        usage = "[message_id]"
    )
    @commands.has_permissions(manage_channels = True, manage_messages = True)
    async def reroll_giveaway(self, ctx, message_id):
        giveaway = get_giveaway(ctx.guild.id, ctx.channel.id, message_id)

        try:
            message = await ctx.channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden):
            embed_failure = discord.Embed(title = "Giveaway End", description = "I didn't found this giveaway in this channel. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        if giveaway == None or message == None or len(message.embeds) == 0:
            embed_failure = discord.Embed(title = "Giveaway Reroll", description = "I didn't found this giveaway in this channel. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        if giveaway[7] == 0:
            embed_failure = discord.Embed(title = "Giveaway Reroll", description = "Giveaway must end for reroll. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        reaction = discord.utils.get(message.reactions, emoji = "🎉")

        if reaction == None or reaction.count == 1:
            embed_failure = discord.Embed(title = "Giveaway Reroll", description = f"I can't pick new winner (Reaction not found or nobody reacted). :x:\n{message.jump_url}", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        users = await reaction.users().flatten()
        users.remove(self.bot.user)

        await ctx.send(f"New winner is {choice(users).mention}, congratulations! :tada:\n{message.jump_url}")

    @commands.command(
        name = "end-giveaway",
        description = "Ends the giveaway",
        usage = "[message_id]"
    )
    @commands.has_permissions(manage_channels = True, manage_messages = True)
    async def end_giveaway(self, ctx, message_id):
        giveaway = get_giveaway(ctx.guild.id, ctx.channel.id, message_id)
        try:
            message = await ctx.channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden):
            embed_failure = discord.Embed(title = "Giveaway End", description = "I didn't found this giveaway in this channel. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        if giveaway == None or message == None or len(message.embeds) == 0:
            embed_failure = discord.Embed(title = "Giveaway End", description = "I didn't found this giveaway in this channel. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        if giveaway[7] == 1:
            embed_failure = discord.Embed(title = "Giveaway End", description = "That giveaway already ended. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        reaction = discord.utils.get(message.reactions, emoji = "🎉")

        if reaction == None or reaction.count == 1:
            return await ctx.send(f"I couldn't determinate the winner (Reaction not found or nobody reacted).\n{message.jump_url}")

        users = await reaction.users().flatten()
        users.remove(self.bot.user)
        winners = []

        for i in range(giveaway[4]):
            if len(users) > 0:
                winner = choice(users)
                winners.append(winner.mention)

                await ctx.send(f"Congratulations, {winner.mention}, you won the **{giveaway[3]}**. :tada:\n{message.jump_url}")
            else:
                await ctx.send(f"I couldn't determinate the winner.\n{message.jump_url}")

        cursor.execute("UPDATE giveaways SET ended = %s WHERE guild_id = %s AND channel_id = %s AND message_id = %s", (True, ctx.guild.id, ctx.channel.id, message_id,))
        db.commit()

        embed_giveaway = message.embeds[0].copy()
        mentions = "\n".join(winners)
        embed_giveaway.description += f"\n\nWinners:\n{mentions}"
        await message.edit(embed = embed_giveaway)

    @commands.command(
        name = "giveaway-list",
        description = "Shows all giveaway on the server",
        usage = "[page (optional)]"
    )
    @commands.has_permissions(manage_channels = True, manage_messages = True)
    async def giveaway_list(self, ctx, page: int = 1):
        giveaways = get_guild_giveaways(ctx.guild.id)
        ln = len(giveaways)
        pages = ceil(ln / GIVEAWAYS_PER_PAGE)

        if page < 1 or page > pages:
            embed_failure = discord.Embed(title = "Giveaway List", description = "Invalid page. :x:", colour = discord.Colour.red())
            embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

            return await ctx.send(embed = embed_failure)

        r1 = (GIVEAWAYS_PER_PAGE * (page - 1))
        r2 = ((GIVEAWAYS_PER_PAGE * page) if (GIVEAWAYS_PER_PAGE * page) <= ln else ln)

        embed_giveaway_list = discord.Embed(title = "Giveaway List", description = "", colour = discord.Colour.blurple())
        embed_giveaway_list.set_footer(text = f"Page: {page} / {pages}")

        count = 1
        for i in range(r1, r2):
            channel = ctx.guild.get_channel(giveaways[i][1])
            if channel == None: continue
            try:
                message = await channel.fetch_message(giveaways[i][2])
            except (discord.NotFound, discord.Forbidden):
                delete_giveaway(giveaways[i][0], giveaways[i][1], giveaways[i][2])
                continue
            embed_giveaway_list.description += f"**{count}.** {message.jump_url}\n\n"
            count += 1

        await ctx.send(embed = embed_giveaway_list)

    @tasks.loop(seconds = 1.0)
    async def giveaway_loop(self):
        giveaways = get_all_giveaways()

        for giveaway in giveaways:
            try:
                guild = self.bot.get_guild(giveaway[0])

                if guild == None:
                    delete_giveaway(giveaway[0], giveaway[1], giveaway[2])
                    continue

                channel = guild.get_channel(giveaway[1])

                if channel == None:
                    delete_giveaway(giveaway[0], giveaway[1], giveaway[2])
                    continue

                message = await channel.fetch_message(giveaway[2])

                if len(message.embeds) == 0:
                    delete_giveaway(giveaway[0], giveaway[1], giveaway[2])
                    continue

                reaction = discord.utils.get(message.reactions, emoji = "🎉")
                users = await reaction.users().flatten()

                if len(giveaway[5]) > 0:
                    args = giveaway[5].split(",")

                    for user in users:
                        if user.bot:
                            continue

                        member = guild.get_member(user.id)
                        user_obj = get_user(user.id)

                        for arg in args:
                            req_args = arg[1:len(arg) - 1].split(":")

                            if req_args[0] != "2": continue
                            if user_obj[4] == None:
                                await message.remove_reaction("🎉", member)
                                    
                                try:
                                    await user.send(f"You need to verify first to join ROBLOX giveaways. :x:\n{message.jump_url}")
                                finally:
                                    continue

                            roblox_cog = self.bot.get_cog("Roblox")
                            roblox_user = await roblox_cog.get_user(user_obj[4])

                            if roblox_user == None:
                                cursor.execute("UPDATE users SET roblox_id = %s WHERE user_id = %s", (None, user.id,))
                                db.commit()

                                await message.remove_reaction("🎉", member)
                                try:
                                    await user.send(f"Your ROBLOX account was not found. :x:\n{message.jump_url}")
                                finally:
                                    continue
    
                            req_args[1] = int(req_args[1])
                            found = False

                            for group in roblox_user["Groups"]:
                                if group["id"] != req_args[1]:
                                    continue

                                found = True
                                break

                            if not found:
                                await message.remove_reaction("🎉", member)

                                try:
                                    await user.send(f"You didn't join the ROBLOX groups. :x:\n{message.jump_url}")
                                except:
                                    pass

                if giveaway[7] == 0 and time.time() >= giveaway[6]:
                    if reaction == None or reaction.count == 1:
                        cursor.execute("UPDATE giveaways SET ended = true WHERE guild_id = %s AND channel_id = %s AND message_id = %s", (giveaway[0], giveaway[1], giveaway[2],))
                        db.commit()

                        await channel.send(f"I couldn't determinate the winner (Reaction not found or nobody reacted).\n{message.jump_url}")
                        continue

                    users.remove(self.bot.user)
                    winners = []

                    for i in range(giveaway[4]):
                        if len(users) > 0:
                            winner = choice(users)
                            winners.append(winner.mention)
                            users.remove(winner)

                    await channel.send(f"Congratulations, {', '.join(winners)}, you won the **{giveaway[3]}**. :tada:\n{message.jump_url}")

                    embed_giveaway = message.embeds[0].copy()
                    mentions = "\n".join(winners)
                    embed_giveaway.description += f"\n\nWinners:\n{mentions}"
                    await message.edit(embed = embed_giveaway)

                    cursor.execute("UPDATE giveaways SET ended = true WHERE guild_id = %s AND channel_id = %s AND message_id = %s", (giveaway[0], giveaway[1], giveaway[2],))
                    db.commit()
            except (discord.NotFound, discord.Forbidden):
                delete_giveaway(giveaway[0], giveaway[1], giveaway[2])
            except Exception as ex:
                print(f"[GIVEAWAY LOOP] {ex}")
def setup(bot):
    bot.add_cog(Giveaways(bot))