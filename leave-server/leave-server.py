import discord
from discord.ext import commands

class LeaveGuildPlugin:
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.is_owner()
    async def leaveguild(self, ctx, guild_id: int):
        try:    
            await self.bot.get_guild(guild_id).leave()
            return ctx.send("Left!")
        except:
            return ctx.send("Error!")
            
    async def on_ready(self):
        async with self.bot.session.post("https://counter.modmail-plugins.ionadev.ml/api/instances/leaveserver", json={'id': self.bot.user.id}):
            print("Posted to Plugin API")          
def setup(bot):
    bot.add_cog(LeaveGuildPlugin(bot))
