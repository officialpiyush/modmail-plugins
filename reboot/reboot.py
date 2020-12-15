import sys
import os
import discord
import logging
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

logger = logging.getLogger('Modmail')


class RebootCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    async def reboot(self, ctx):
        """Clears Cached Logs & Reboots The Bot"""
        msg = await ctx.send(embed=discord.Embed(
            color=discord.Color.blurple(),
            description="Processing..."
        ))

        # Clear The cached logs
        #with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
       #                        '../../../temp/logs.log'), 'w'):
          #  pass
        await ctx.invoke(self.bot.get_command('debug clear'))
        emsg = await msg.edit(embed=discord.Embed(
            color=discord.Color.blurple(),
            description="✅ Cleared Cached Logs"
        ))
        logger.info("==== Rebooting Bot ====")
        await msg.edit(embed=discord.Embed(
            color=discord.Color.blurple(),
            description="`✅ | Cleared Cached Logs`\n\n`✅ | Rebooting....`"
        ))
        os.execl(sys.executable, sys.executable, * sys.argv)


def setup(bot):
    bot.add_cog(RebootCog(bot))
