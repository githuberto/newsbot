"""
A simple logging module for logging to both the logging library and Discord.
"""
import discord
import inspect
import logging


from discord import app_commands
from discord.ext import commands
from typing import Optional, Union


# A type alias for an optional Context or Interaction param.
Ctx = Optional[Union[commands.Context, discord.Interaction]]


async def log(message: str, /, *, ctx: Ctx = None, ephemeral: bool = True,
              level: int = logging.INFO):
  """Logs a message to the logging library and an optional Discord context."""

  # Log using the filename of the caller if available.
  stack = inspect.stack()
  if not stack:
    logger = logging.getLogger(__name__)
    logger.error(
        f"Unable to get caller's stack. Logging as {__name__} instead.")
  else:
    logger = logging.getLogger(stack[0].filename)
  logger.log(level, message)

  # If ctx is provided, ensure it's a Context and reply.
  if not ctx:
    return
  if isinstance(ctx, discord.Interaction):
    ctx = await commands.Context.from_interaction(ctx)
  await ctx.reply(message, ephemeral=ephemeral)
