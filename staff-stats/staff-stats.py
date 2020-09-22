import asyncio

from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class StaffStatsPlugin(commands.Cog):
    """
    Just a plugin which saves staff IDs in the database for frontend stuff.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        bot.loop.create_task(self._update_stats())

    async def _update_stats(self):
        while True:
            category = self.bot.get_channel(
                int(self.bot.config.get("main_category_id"))
            )

            staff_members = list()

            for member in self.bot.modmail_guild.members:
                if member.permissions_in(category).read_messages:
                    if not member.bot:
                        staff_members.append(str(member.id))

            await self.db.find_one_and_update(
                {"_id": "list"}, {"$set": {"staff": staff_members}}, upsert=True
            )

            await asyncio.sleep(86400)

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def syncstaff(self, ctx):
        """
        Sync Staff
        """
        category = self.bot.get_channel(int(self.bot.config.get("main_category_id")))

        staff_members = list()

        for member in self.bot.modmail_guild.members:
            if member.permissions_in(category).read_messages:
                if not member.bot:
                    staff_members.append(str(member.id))

        await self.db.find_one_and_update(
            {"_id": "list"}, {"$set": {"staff": staff_members}}, upsert=True
        )

        await ctx.send("Done.")
        return


def setup(bot):
    bot.add_cog(StaffStatsPlugin(bot))
