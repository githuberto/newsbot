"""
A base cog module with examples text, app (slash), and hybrid (both) commands.
"""
import discord
import feedparser
import logging
import traceback
import time
import typing


from bs4 import BeautifulSoup, Tag, NavigableString
from cfg import cfg
from db import db
from logger import log
from discord import app_commands
from discord.ext import commands, tasks


class NewsbotCog(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.sync_feeds.start()

  @tasks.loop(seconds=60 * 60)
  async def sync_feeds(self):
    feeds = db.select("feeds", ["id"])
    for feed in feeds:
      await self.sync(feed["id"])

  async def cog_app_command_error(self, itx: discord.Interaction,
                                  exc: Exception):
    await log("".join(traceback.format_exception(exc)), level=logging.ERROR)

    content = f"**Error:**\n```py\n{exc}```"
    if itx.response.is_done():
      await itx.followup.send(content)
    else:
      await itx.response.send_message(content)

  def embed_from_post(self, post) -> discord.Embed:
    # Parse the summary and image from the post.
    soup = BeautifulSoup(post.summary, features="html.parser")
    paragraph = soup.find("p")
    if isinstance(paragraph, Tag) and paragraph.contents:
      summary = str(paragraph.contents[0])
    elif isinstance(paragraph, NavigableString):
      summary = str(paragraph)
    else:
      summary = "Summary Missing"
    img = soup.find("img")

    image_link = img.get("src", "") if img and isinstance(img, Tag) else ""

    embed = discord.Embed(title=post.title)
    embed.description = summary
    embed.url = post.link
    # embed.set_image(url=image_link)
    embed.set_thumbnail(url=image_link)
    embed.set_footer(
        text=time.strftime("Published %B %d, %Y", post.published_parsed))

    return embed

  def get_new_posts(self, feed_id: int, url: str) -> list:
    d = feedparser.parse(url)
    past_posts = db.select("posts", ["id"], {"feed_id": feed_id})
    past_ids = {p["id"] for p in past_posts}

    return [e for e in reversed(d.entries) if e.id not in past_ids]

  async def sync(self, feed_id: int):
    rows = db.select("feeds", ["*"], {"id": feed_id})
    if not rows:
      raise KeyError(f"Feed with id {id} was not found!")
    row = rows[0]
    channel = self.bot.get_channel(row["channel"])
    if not channel:
      raise KeyError(
          f"Channel {row['channel']} was not found for {row}!")
    channel = typing.cast(discord.TextChannel, channel)

    new_posts = self.get_new_posts(feed_id, row["url"])

    successful_post_ids = []
    embeds = []
    for p in new_posts:
      embeds.append(self.embed_from_post(p))
      successful_post_ids.append(p.id)

    # Send in batches of 10 until all embeds are posted.
    for post_id, embed in zip(successful_post_ids, embeds):
      await channel.send(embed=embed)
      db.insert("posts", {"id": post_id, "feed_id": feed_id})

  @app_commands.command()
  @app_commands.guilds(*cfg.guilds)
  async def list_feeds(self, itx: discord.Interaction):
    if not itx.guild:
      await itx.response.send_message(
          "This must be run from a guild!", ephemeral=True)
      return

    rows = db.select("feeds", ["*"])
    embed = discord.Embed(title="News Feeds")
    embed.colour = discord.Colour.blue()
    for row in rows:
      content = "\n".join([
          row['url'],
          f"`Channel`: <#{row['channel']}>"])
      embed.add_field(
          name=f"Feed #{row['id']}",
          value=content)

    await itx.response.send_message(embed=embed)

  @app_commands.command()
  @app_commands.guilds(*cfg.guilds)
  async def add_feed(self, itx: discord.Interaction, url: str,
                     channel: discord.TextChannel):
    """Adds a new RSS feed to sync to a channel.

    Args:
      url: The RSS feed URL.
      channel: The channel this feed should be synced to.
    """
    await itx.response.defer()

    id = db.insert("feeds", {
        "url": url,
        "channel": channel.id})

    await self.sync(id)
    await itx.followup.send(f"Added {url} to {channel.mention}!")

  @app_commands.command()
  @app_commands.guilds(*cfg.guilds)
  async def remove_feed(self, itx: discord.Interaction, id: int):
    """Removes an RSS feed.

    Args:
      id: The id of the feed as shown in /list_feeds.
    """
    if db.delete("feeds", {"id": id}):
      await itx.response.send_message(f"Feed `{id}` was deleted.")
    else:
      await itx.response.send_message(f"No feed found with id `{id}`.")


async def setup(bot: commands.Bot):
  await bot.add_cog(NewsbotCog(bot))
