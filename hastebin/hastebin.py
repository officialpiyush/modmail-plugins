import discord
import os
from discord import Embed
from discord.ext import commands

from json import JSONDecodeError
from aiohttp import ClientResponseError

Cog = getattr(commands, "Cog" , object)

class HastebinCog(Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def hastebin(self,ctx,*,message):
        """Upload Text To hastebin"""
        haste_url = os.environ.get('HASTE_URL', 'https://hasteb.in')

        try:
            async with self.bot.session.post(haste_url + '/documents',data=message) as resp:
                key = (await resp.json())["key"]
                embed = Embed(
                    title='Your Uploaded File',
                    color=self.bot.main_color,
                    description=f'{haste_url}/' + key
                )
        except (JSONDecodeError, ClientResponseError, IndexError):
            embed = Embed(
                color=self.bot.main_color,
                description='Something\'s wrong. '
                            'We\'re unable to upload your text to hastebin.'
            )
            embed.set_footer(text='Hastebin Plugin')
        await ctx.send(embed=embed)
    @Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post("https://counter.modmail-plugins.ionadev.ml/api/instances/hastebin", json={'id': self.bot.user.id}):
            print("Posted to Plugin API")

def setup(bot):
    bot.add_cog(HastebinCog(bot))
