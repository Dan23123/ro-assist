import discord
import html

from discord.ext import commands
from googleapiclient.discovery import build
from config import YOUTUBE_TOKEN
from typing import Optional

class Youtube(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.youtube = build("youtube", "v3", developerKey = YOUTUBE_TOKEN)

	@commands.command(
		name = "search-youtube",
		description = "Search for videos on youtube",
		usage = "[max_results (default = 10)] [name]"
	)
	async def searchyoutube(self, ctx, max_results: Optional[int] = 10, *, name):
		if max_results < 1 or max_results > 25:
			embed_failure = discord.Embed(title = "Youtube Search", description = "Max Results amount must be between 1 and 25. :x:", colour = discord.Colour.red())
			embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))

			return await ctx.send(embed = embed_failure)

		response = self.search_request(name, max_results)

		embed_videos = discord.Embed(title = "Youtube Search", colour = discord.Colour.red())
		video_count = 0

		for video in response["items"]:
			if video_count == max_results:
				break

			if "videoId" in video["id"]:
				video_count += 1
				embed_videos.add_field(name = f"{video_count}. {video['snippet']['title']}", value = f"https://www.youtube.com/watch?v={video['id']['videoId']}", inline = False)

		if video_count > 0:
			await ctx.send(embed = embed_videos)
		else:
			embed_failure = discord.Embed(title = "Youtube Search", description = "Videos not found. :x:", colour = discord.Colour.red())
			embed_failure.set_author(name = ctx.author, icon_url = str(ctx.author.avatar_url))
			await ctx.send(embed = embed_failure)

	def search_request(self, name, max_results):
		request = self.youtube.search().list(
			part = "snippet",
			q = name,
			maxResults = max_results
		)
		response = request.execute()

		for i in range(len(response["items"])):
			response["items"][i]["snippet"]["title"] = html.unescape(response["items"][i]["snippet"]["title"])

		return response

def setup(bot):
	bot.add_cog(Youtube(bot))