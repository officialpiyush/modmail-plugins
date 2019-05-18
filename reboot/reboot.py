import sys
import os
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
        await ctx.send("Rebooting The Bot...")
        print("========== Rebooting ==========")
        os.execl(sys.executable, sys.executable, * sys.argv)


def setup(bot):
    bot.add_cog(RebootCog(bot))