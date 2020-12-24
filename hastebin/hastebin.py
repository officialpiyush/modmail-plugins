import discord
import os
from discord import Embed
from discord.ext import commands

from json import JSONDecodeError
from aiohttp import ClientResponseError


class HastebinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hastebin(self, ctx, *, message):
        """Upload text to hastebin"""
        haste_url = os.environ.get("HASTE_URL", "https://hastebin.cc")

        try:
            async with self.bot.session.post(
                haste_url + "/documents", data=message
            ) as resp:
                key = (await resp.json())["key"]
                embed = Embed(
                    title="Your uploaded file",
                    color=self.bot.main_color,
                    description=f"{haste_url}/" + key,
                )
        except (JSONDecodeError, ClientResponseError, IndexError):
            embed = Embed(
                color=self.bot.main_color,
                description="Something went wrong. "
                "We're unable to upload your text to hastebin.",
            )
            embed.set_footer(text="Hastebin Plugin")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post(
            "https://counter.modmail-plugins.piyush.codes/api/instances/hastebin",
            json={"id": self.bot.user.id},
        ):
            print("Posted to Plugin API")


def setup(bot):
    bot.add_cog(HastebinCog(bot))
