import sys
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class RebootCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    async def reboot(self, ctx):
        """Reboots The Bot"""
        await ctx.send("Rebooting The Bot..")
        sys.exit()


def setup(bot):
    bot.add_cog(RebootCog(bot))