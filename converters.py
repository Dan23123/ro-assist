from discord.ext import commands

class TimeConverter(commands.Converter):
	async def convert(self, ctx, argument) -> int:
		argument = argument.lower()
		try:
			if argument.endswith("s"):
				return int(argument[:len(argument) - 1])
			elif argument.endswith("m"):
				return int(argument[:len(argument) - 1]) * 60
			elif argument.endswith("h"):
				return int(argument[:len(argument) - 1]) * 60 * 60
			elif argument.endswith("d"):
				return int(argument[:len(argument) - 1]) * 24 * 60 * 60
			else:
				return int(argument)
		except ValueError:
			pass