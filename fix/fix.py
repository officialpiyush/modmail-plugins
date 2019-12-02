import discord
from discord.ext import commands

from core.models import PermissionLevel
from core import checks


class TopicFixPlugin(commands.Cog):
    """
    Fix all threads with broken channel topic
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["f"])
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    async def fix(self, ctx):
        """
        Fix a broken thread. (Works only in thread channels.)

        **Usage:**
        {prefix}fix
        """

        await ctx.channel.edit(topic=f"User ID: {ctx.thread._id}")
        await ctx.send("Done!")
        return

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.session.post(
                "https://counter.modmail-plugins.piyush.codes/api/instances/fix",
                json={"id": self.bot.user.id},
        ):
            print("Posted to Plugin API")


def setup(bot):
    bot.add_cog(TopicFixPlugin(bot))
