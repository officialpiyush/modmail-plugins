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
    async def fix(self, ctx):
        """
        Fix a broken thread

        **Usage:**
        {prefix}fix
        """
        genesis_message = await ctx.channel.history(
            oldest_first=True, limit=1
        ).flatten()
        if (
            genesis_message[0].embeds
            and genesis_message[0].embeds[0]
            and genesis_message[0].embeds[0].footer.text
            and "User ID:" in genesis_message[0].embeds[0].footer.text
        ):
            await ctx.channel.edit(
                topic=f"User ID: {genesis_message[0].embeds[0].footer.text}",
                reason=f"Fix the thread. Command used by {ctx.author.name}#{ctx.author.discriminator}",
            )
            await ctx.send("Fixed the thread.")
        else:
            await ctx.send("This channel doesn't seem like a modmail thread.")
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
