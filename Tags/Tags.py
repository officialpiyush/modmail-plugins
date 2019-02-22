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
            return
    
    @tags.command(name="add")
    async def add_(self, ctx, name, *, content):
            await self.db.find_one_and_update(
            {'_id': 'tags'},
            {'$set': {name: {'info': content, 'user_id': str(ctx.author.id)}}},
            upsert=True
            )
            await ctx.send(f"A tag with `{name}` has been created succesfully!")
        
    @commands.command
    async def tag(self,ctx,arg):
        await ctx.send("nou")
       

def setup(bot):
    bot.add_cog(TagPlugin(bot))
