import discord
from discord.ext import commands

class DmOnJoinPlugin:
    def __init__(self,bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
    
    @commands.command(aliases=["sdms"])
    @commands.has_permissions(manage_guild=True)
    async def setdmmessage(self,ctx,*,message):
        """Set A Message To DM A user after they join."""
        if message.startswith('https://') or message.startswith('http://'):
            # message is a URL
            if message.startswith('https://hasteb.in/'):
                message = 'https://hasteb.in/raw/' + message.split('/')[-1]

            async with self.bot.session.get(message) as resp:
                message = await resp.text()
        await self.db.find_one_and_update(
        {'_id': 'dm-config'},
        {'$set': {'dm-message': {'message': message}}},
        upsert=True
        )

        await ctx.send("Successfully Set The Message.")
    
    async def on_member_join(self,member):
        config = (await self.db.find_one({'_id': 'dm-config'}))['dm-message']
        if config is None:
            return
        else:
            try:
                await member.send(config["message"])
            except: 
                return
    
    async def on_ready(self):
        async with self.bot.session.post("https://counter.modmail-plugins.ionadev.ml/api/instances/dmonjoin", json={'id': self.bot.user.id}):
            print("Posted to Plugin API")
    
def setup(bot):
    bot.add_cog(DmOnJoinPlugin(bot))
