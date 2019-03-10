import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure

class AnnoucementPlugin:
    def __init__(self,bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)

    @commands.command(aliases=['setAnnouncementChannel'])
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
    @has_permissions(manage_messages=True)
    async def announce(self,ctx,*,message):
        config = (await self.db.find_one({'_id': 'a-config'}))['announcement']
        if config is None:
            await ctx.send("No Channel Configured!")
        else:
            channel = ctx.guild.get_channel(int(config['channel']))
            if channel:
                await channel.send(message)
            else:
                await ctx.send(f"No {channel.id} Found!")

    # permission Handling
    @sac.error
    async def sac_error(self,error,ctx):
         if isinstance(error, CheckFailure):
             await self.bot.send_message(ctx.message.channel, "Looks like you don't have the perm.")

def setup(bot):
    bot.add_cog(AnnoucementPlugin(bot))
