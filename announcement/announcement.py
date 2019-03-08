import discord
from discord.ext import commands

class AnnoucementPlugin:
    def __init__(self,bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.command()
    async def setAnnouncementChannel(self,ctx, channel: discord.TextChannel):
        await self.db.find_one_and_update(
        {'_id': 'config'},
        {'$set': {'announcement': {'channel': ctx.channel.id}}},
        upsert=True
        )
        await ctx.send(f"{channel.mention} set for announcements!")

    @commands.command()
    async def announce(self,ctx,*,message):
        config = (await self.db.find_one({'_id': 'config'}))['announcement']
        if config:
            channel = ctx.guild.get_channel(int(config['channel']))
            if channel:
                await channel.send(message)
            else:
                await ctx.send(f"No {channel.id} Found!")
        else:
            ctx.send("Not Configured!")

def setup(bot):
    bot.add_cog(AnnoucementPlugin(bot))
