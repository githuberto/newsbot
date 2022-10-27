"""A cog module which provides commands for syncing app (slash) commands."""
import discord


from cfg import cfg
from discord import app_commands
from discord.ext import commands
from logger import log


@app_commands.guilds(*cfg.guilds)
class SyncCog(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @commands.hybrid_command()
  @app_commands.guilds(*cfg.guilds)
  async def sync(self, ctx: commands.Context):
    """Sync the bot's command tree to the guild it's run in.

    NOTE: Only needed on command changes. This is heavily rate limited!!!
    """
    if not ctx.guild:
      await ctx.reply("This command must be run in a guild!", ephemeral=True)
      return

    await ctx.defer()
    await self.bot.tree.sync(guild=ctx.guild)
    await ctx.reply(f"Successfully synced to `{ctx.guild}`!", ephemeral=True)


async def setup(bot: commands.Bot):
  await bot.add_cog(SyncCog(bot))
