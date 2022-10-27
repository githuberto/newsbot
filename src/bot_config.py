"""
A module which defines the bot's config dataclass.

This is separated from the actual config data in cfg.py so that the config
definition can be included in version control without including the actual
Discord token, ids, etc.
"""
from dataclasses import dataclass


@dataclass
class BotConfig():
  discord_token: str  # The Discord token for you bot.
  guilds: list[int]   # The list of guilds for guild-only commands.
  dev_id: int = 0     # Your Discord id if you want to DM errors to yourself.
  prefix: str = "!"   # The prefix for your bot's text commands.
