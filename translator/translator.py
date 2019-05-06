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
                await ctx.send("Couldnt Find An Embed in that message.")
            
            embed = msg.embeds[0]
            tmsg = self.translator.translate(embed.description)
            rembed = discord.Embed()
            rembed.description = tmsg.text
            await ctx.channel.send(embed=rembed)
        except NotFound:
            await ctx.send("The Given Message Was Not Found.")
        except HTTPException:
            await ctx.send("The Try To Retrieve The Message Failed.")

def setup(bot):
    bot.add_cog(TranslatePlugin(bot))
