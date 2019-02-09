import discord
from discord.ext import commands

class TagPlugin:
    def __init__(self,bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.command()
    async def iona(self,ctx):
        await ctx.send('A Plugin Created to server your need for tags!')
    
    @commands.group()
    async def tags(self,ctx):
        if ctx.invoked_subcommand is None:
            cmd = self.bot.get_command('help')
            await ctx.invoke(cmd,command="tags")
    
    @tags.command(name="add")
    async def add_(self,ctx,*,message: commands.clean_content):
       message = message.split("||")
       print(message)
       # tag = await self.db.find_one({'tagName': message[0]})

def setup(bot):
    bot.add_cog(TagPlugin(bot))
