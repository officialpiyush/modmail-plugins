import discord
from discord.ext import commands

class TagPlugin:
    def __init__(self,bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
    
    @commands.group()
    async def tags(self,ctx):
        if ctx.invoked_subcommand is None:
            return
    
    @tags.command(name="add")
    @commands.has_permissions(manage_messages=True)
    async def add_(self, ctx, name, *, content):
            await self.db.find_one_and_update(
            {'_id': 'tags'},
            {'$set': {name: {'info': content, 'user_id': str(ctx.author.id)}}},
            upsert=True
            )
            await ctx.send(f":white_check_mark: | A tag with `{name}` has been created succesfully!")
    
    # @tags.command(name="info")
    # @commands.has_permissions(manage_messages=True)
    # async def info(self,ctx,tagName):
    #     tagCollection = await self.db.find_one({"_id": "tags"})
    #     tag = tagCollection[tagName]
    #     if tag is None:
    #         await ctx.send(f":x: | Tag `{tagName}` Not Found")
    #         return
        
    @tags.command(name="delete")
    @commands.has_permissions(manage_messages=True)
    async def delete(self,ctx,tagName):
        try:
            config = (await self.db.find_one({"_id": "tags"}))[tagName]
            if config is None:
                await ctx.send(":x: | Tag Not Found")
                return
            await self.db.delete_one(config)
        except:
            await ctx.send(":x: | Something Wrong Happened While Deleting The Tag")
        
    @commands.command()
    async def tag(self,ctx,tagName):    
        config = (await self.db.find_one({"_id": "tags"}))[tagName]
        if config is None:
            await ctx.send(":x: | Tag Not Found")
            return
        await ctx.send(config.content)
        return

    @tags.command(name="update")   
    @commands.has_permissions(manage_messages=True)
    async def update(self,ctx,tagName,*,msg):
        try:
            config = (await self.db.find_one({"_id": "tags"}))[tagName]
            if config is None:
                await ctx.send(":x: | Tag Not Found")
            await self.db.find_one_and_update(
            {'_id': 'tags'},
            {'$set': {tagName: {'info': msg, 'user_id': str(ctx.author.id)}}},
            )
            await ctx.send(f":white_check_mark: | Tag `{tagName}` updated Successfully")
        except:
            await ctx.send(":x: | Something Wrong Happened While Updating The Tag")
    async def on_ready(self):
        async with self.bot.session.post("https://counter.modmail-plugins.ionadev.ml/api/instances/tags", content_type='application/json',json={'id': self.bot.user.id}):
            pass
            
def setup(bot):
    bot.add_cog(TagPlugin(bot))
