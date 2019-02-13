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
    @checks.has_permissions(manage_messages=True)
    async def tags(self,ctx):
        if ctx.invoked_subcommand is None:
            return
    
    @tags.command(name="add")
    async def add_(self,ctx,name, *,info):
        if name is None:
            await ctx.send('Please Give US The name Of tag')
        elif info is None:
            await ctx.send(f"Please Give us the Content of {name} tag and try again.")
        else:
            try:
                await self.db.find_one_and_update(
                {'_id': 'tags'},
                {'$set': {str(name): {info: str(info), user_id: str(ctx.author.id)}}},
                upsert=True
                )
                await ctx.send(f"A tag with `{name} has been created succesfully!`")
            except:
                ctx.send('There Was AN Error Please try Again!')
       

def setup(bot):
    bot.add_cog(TagPlugin(bot))
