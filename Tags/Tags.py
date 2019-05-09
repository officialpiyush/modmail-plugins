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
    
    @tags.command(name='add')
    @commands.has_permissions(manage_messages=True)
    async def add_(self, ctx, name, *, content):
        '''Add an extra tag to your existing tags.'''

        name = name.lower()

        await self.db.insert_one({
            'name': name,
            'content': content,
            'creator': ctx.author.name,
            'uses': 0
        })

        await ctx.send(f':white_check_mark: | A tag `{name}` has been created succesfully!')
    
    @tags.command(name='info')
    @commands.has_permissions(manage_messages=True)
    async def info(self, ctx, tag_name):
        '''Get info on a specific tag.'''

        tag = await self.db.find_one({'name': tag_name})

        if tag is None:
            return await ctx.send(f':x: | Tag `{tag_name}` not found.')
        
        await ctx.send(
            f'Tag `{tag_name}` has been made by ' + tag['creator'] + 
            ' and has been used ' + str(tag['uses']) + ' times.'
        )
            
        
    @tags.command(name='delete')
    @commands.has_permissions(manage_messages=True)
    async def delete(self, ctx, tag_name):
        '''Delete an existing tag.'''

        try:
            tag = await self.db.find_one({'name': tag_name})

            if tag is None:
                return await ctx.send(':x: | Tag not found.')

            await self.db.delete_one(tag)

            await ctx.send(f'Tag `{tag_name}` has been deleted successfully.')
        except:
            await ctx.send(':x: | An error occurred while trying to delete the tag.')

    @tags.command(name='list')
    async def list_(self, ctx):
        '''Get a list of tags that hace already been made.'''

        tags = await self.db.find({}).to_list(length=None)

        if tags is None:
            return await ctx.send(':x: | You don't have any tags.')
        
        list_tags = []

        for tag in tags:
            try:
                list_tags.append(tag['name'])
            except:
                continue

        send_tags = '\n'.join(list_tags)

        await ctx.send(send_tags)

    @commands.command()
    async def tag(self, ctx, tag_name):
        '''Get a tag that has already been made.'''

        tag = await self.db.find_one({'name': tag_name})

        if tag is None:
            return await ctx.send(':x: | Tag not found.')

        await self.db.find_one_and_update(
                {'name': tag_name},
                {'$set': {'uses': tag['uses'] + 1}},
            )

        await ctx.send(tag['content'])

    @tags.command(name='update')   
    @commands.has_permissions(manage_messages=True)
    async def update(self, ctx, tag_name, *, content):
        '''Update the content of an existing tag.'''

        try:
            config = (await self.db.find_one({'name': tag_name}))

            if config is None:
                await ctx.send(':x: | Tag not found.')

            await self.db.find_one_and_update(
                {'name': tag_name},
                {'$set': {'content': content, 'creator': ctx.author.name}},
            )

            await ctx.send(f':white_check_mark: | Updated tag `{tag_name}` successfully.')
        except:
            await ctx.send(':x: | An error occurred while deleting the tag.')

def setup(bot):
    bot.add_cog(TagPlugin(bot))
