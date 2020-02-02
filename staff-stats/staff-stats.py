import asyncio

from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class StaffStatsPlugin(commands.Cog):
    """
  Just a plugin which saves staff statistics in the database for frontend stuff.
  """

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        bot.loop.create_task(self._update_stats())

    async def _update_stats(self):
        while True:
            staff_list = list()

            category = self.bot.get_channel(
                int(self.bot.config.get("main_category_id"))
            )

            # L28 - L30 taken from https://github.com/papiersnipper/modmail-plugins/blob/daa6e31356030cb35ef12e4cf0e1df7015065798/supporters/supporters.py#L47-L49
            for member in self.bot.modmail_guild.members:
                if member.permissions_in(category).read_messages:
                    if not member.bot:
                        responded = await self.bot.api.get_responded_logs(member.id)
                        closed = await self.bot.db.logs.find(
                            {
                                "guild_id": str(self.bot.guild_id),
                                "open": False,
                                "closer.id": str(member.id),
                            },
                            {"messages": {"$slice": 5}},
                        ).to_list(None)
                        staff_list.append(
                            {
                                "username": str(member),
                                "id": member.id,
                                "closed": len(tuple(closed)),
                                "responded": len(tuple(responded)),
                                "avatar": str(member.avatar_url),
                            }
                        )

            await self.db.find_one_and_update(
                {"_id": "config"}, {"$set": {"staff": staff_list}}, upsert=True
            )

            await asyncio.sleep(86400)

    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def syncstaff(self, ctx):
        """
         Sync Staff
        """

        staff_list = list()

        category = self.bot.get_channel(int(self.bot.config.get("main_category_id")))

        # L68 - L70 taken from https://github.com/papiersnipper/modmail-plugins/blob/daa6e31356030cb35ef12e4cf0e1df7015065798/supporters/supporters.py#L47-L49
        for member in self.bot.modmail_guild.members:
            if member.permissions_in(category).read_messages:
                if not member.bot:
                    responded = await self.bot.api.get_responded_logs(member.id)
                    closed = await self.bot.db.logs.find(
                        {
                            "guild_id": str(self.bot.guild_id),
                            "open": False,
                            "closer.id": str(member.id),
                        },
                        {"messages": {"$slice": 5}},
                    ).to_list(None)
                    staff_list.append(
                        {
                            "username": str(member),
                            "id": member.id,
                            "closed": len(tuple(closed)),
                            "responded": len(tuple(responded)),
                            "avatar": str(member.avatar_url),
                        }
                    )

        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"staff": staff_list}}, upsert=True
        )

        await ctx.send("Done.")
        return


def setup(bot):
    bot.add_cog(StaffStatsPlugin(bot))
