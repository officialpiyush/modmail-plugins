import discord
from discord.ext import commands

class LeaveGuildPlugin:
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.is_owner()
    async def leaveguild(self, ctx, guild_id):
        try:
            toleave = self.bot.get_guild(guild_id)
            await toleave.leave()
            ctx.send("Left!")
        except:
            ctx.send("Error!")
            
def setup(bot):
    bot.add_cog(LeaveGuildPlugin(bot))