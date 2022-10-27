"""
The main module which creates the bot and adds each cog inside cogs/.

Usage:
  . venv/bin/activate
  python3 main.py
"""
import asyncio
import discord
import logging
import os


from cfg import cfg
from discord.ext import commands, tasks
from logger import log


class LoaderBot(commands.Bot):
  """A Bot subclass which loads all cogs in cogs/ once the bot is ready."""
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.on_first_ready.start()

  async def on_command_error(self, ctx: commands.Context,
                             exc: commands.CommandError):
    """Ignores annoying not found errors"""
    if isinstance(exc, commands.errors.CommandNotFound):
      return

    raise exc

  @tasks.loop(count=1)
  async def on_first_ready(self):
    """Waits for the bot to be ready and then loads all the cogs in cogs/.

    This is preffered over using on_ready() since that method may be called
    multiple times by discord.py.

    The discord.ext.tasks module is used rather than asyncio.create_task()
    because the tasks module hooks into discord.py's logging while asyncio
    task exceptions are silently ignored by default.
    """
    await self.wait_until_ready()

    await log("Bot is ready. Loading cogs...")
    for fn in os.listdir("cogs"):
      if not fn.endswith(".py"):
        continue
      await self.load_extension(f"cogs.{fn[:-3]}")
      await log(f"loaded {fn}.")

    guilds = []
    for gid in cfg.guilds:
      g = self.get_guild(gid)
      if not g:
        await log(f"Skipping missing guild with id `{gid}`...",
                  level=logging.WARN)
        continue
      guilds.append(g)
    guild_list = ", ".join(map(str, guilds))
    await log(f"Cog load complete. Running in: {guild_list}")


async def main():
  discord.utils.setup_logging()

  intents = discord.Intents.default()
  intents.message_content = True  # Required for text commands.
  bot = LoaderBot(cfg.prefix, intents=intents)

  async with bot:
    await bot.start(cfg.discord_token)


asyncio.run(main())
