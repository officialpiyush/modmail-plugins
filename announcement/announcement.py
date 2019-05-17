import discord
from discord.ext import commands
from .utils import checks

Cog = getattr(commands, 'Cog', object)

class AnnoucementPlugin(Cog):
    def __init__(self,bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.command(aliases=['setAnnouncementChannel'])
    @checks.has_permissions(manage_messages=True)
    async def sac(self,ctx,channel: discord.TextChannel):
        """Set Up The Announcement Channel
        """
        await self.db.find_one_and_update(
        {'_id': 'a-config'},
        {'$set': {'announcement': {'channel': str(channel.id)}}},
        upsert=True
        )
        await ctx.send(f"{channel.mention} set for announcements!")

    @commands.command()
    @checks.has_permissions(manage_messages=True)
    async def announce(self,ctx,*,message):
        """Announce A Message
        """
        config = (await self.db.find_one({'_id': 'a-config'}))['announcement']
        if config is None:
            await ctx.send("No Channel Configured!")
        else:
            channel = ctx.guild.get_channel(int(config['channel']))
            if channel:
                await channel.send(message)
            else:
                await ctx.send(f"No {channel.id} Found!")
    
    @Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post("https://counter.modmail-plugins.ionadev.ml/api/instances/announcement", json={'id': self.bot.user.id}):
            print("Posted to Plugin API")

def setup(bot):
    bot.add_cog(AnnoucementPlugin(bot))
