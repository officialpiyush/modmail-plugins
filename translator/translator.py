import discord
from discord.ext import commands
from discord import NotFound, HTTPException

from googletrans import Translator

class TranslatePlugin:
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()

    @commands.command()
    async def translate(self,ctx,msgid: int):
        try:
            msg = await ctx.channel.get_message(msgid)
            if not msg.embeds:
                ms = msg.content
            else:
                ms = msg.embeds[0].description
            
            embed = msg.embeds[0]
            tmsg = self.translator.translate(ms)
            embed = discord.Embed()
            embed.color = 4388013
            embed.description = tmsg.text
            await ctx.channel.send(embed=embed)
        except NotFound:
            await ctx.send("The Given Message Was Not Found.")
        except HTTPException:
            await ctx.send("The Try To Retrieve The Message Failed.")

    @commands.command(aliases=["tt"])
    async def translatetext(self,ctx,*,message):
        tmsg = self.translator.translate(message)
        embed = discord.Embed()
        embed.color = 4388013
        embed.description = tmsg.text
        await ctx.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(TranslatePlugin(bot))
