import discord
from discord.ext import commands

class DmOnJoinPlugin:
    def __init__(self,bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
    
    @commands.command(aliases=["sdms"])
    @commands.check(administrator=True)
    async def setdmmessage(self,ctx,*,message):
        """Set A Message To DM A user after they join."""
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
                member.send(config["message"])
            except: 
                return
    
def setup(bot):
    bot.add_cog(DmOnJoinPlugin(bot))
